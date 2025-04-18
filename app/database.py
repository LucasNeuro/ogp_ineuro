from typing import Dict, Any, Optional, List
import os
from datetime import datetime
import requests
import json
import uuid

class DatabaseClient:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key must be set in environment variables")
        
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make a request to Supabase API"""
        url = f"{self.supabase_url}/rest/v1/{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            # Para GET, retorna a lista/objeto diretamente
            if method == "GET":
                return result if result else []
                
            # Para POST/PUT, retorna o primeiro item se for uma lista
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Error making request to Supabase: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response text: {e.response.text}")
            return {}

    async def get_or_create_conversation(self, sender_id: str, source: str = "web") -> Dict[str, Any]:
        """
        Obtém ou cria uma nova conversa para o usuário
        
        Args:
            sender_id: ID do usuário (session_id ou número do WhatsApp)
            source: Origem da conversa ('web' ou 'whatsapp')
        """
        try:
            # Tenta buscar conversa existente
            result = self._make_request(
                "GET",
                f"conversations?sender_id=eq.{sender_id}"
            )
            
            if result and len(result) > 0:
                return result[0]
            
            # Cria nova conversa se não existir
            new_conversation = {
                "id": str(uuid.uuid4()),
                "sender_id": sender_id,
                "source": source,
                "content": {
                    "messages": [],
                    "context": {},
                    "metadata": {
                        "source": source,
                        "message_count": 0
                    }
                }
            }
            
            return self._make_request("POST", "conversations", new_conversation)
            
        except Exception as e:
            print(f"Error getting/creating conversation: {e}")
            return {}

    async def add_message_to_conversation(
        self,
        sender_id: str,
        message: str,
        is_user: bool,
        llm_response: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Adiciona uma mensagem à conversa do usuário
        
        Args:
            sender_id: ID do usuário
            message: Mensagem original
            is_user: Se True, é mensagem do usuário, se False, do LLM
            llm_response: Resposta do LLM com metadados (opcional)
        """
        try:
            # Obtém a conversa
            conversation = await self.get_or_create_conversation(sender_id)
            if not conversation:
                raise Exception("Failed to get/create conversation")
            
            # Prepara a nova mensagem
            new_message = {
                "timestamp": datetime.utcnow().isoformat(),
                "is_user": is_user,
                "message": message
            }
            
            # Se for resposta do LLM, adiciona os metadados
            if not is_user and llm_response:
                new_message.update({
                    "llm": llm_response.get("llm", ""),
                    "model": llm_response.get("model", ""),
                    "classification": llm_response.get("classification", ""),
                    "metadata": llm_response.get("metadata", {})
                })
            
            # Atualiza o content da conversa
            content = conversation.get("content", {})
            if not isinstance(content, dict):
                content = {"messages": []}
            
            if "messages" not in content:
                content["messages"] = []
            
            # Adiciona a nova mensagem
            content["messages"].append(new_message)
            
            # Atualiza metadados
            content["metadata"] = {
                **(content.get("metadata", {})),
                "message_count": len(content["messages"])
            }
            
            # Atualiza a conversa no banco usando PATCH e sender_id
            update_data = {
                "content": content
            }
            
            # Modifica os headers para usar PATCH
            patch_headers = {**self.headers}
            patch_headers["Prefer"] = "return=representation"
            
            # Faz a requisição PATCH diretamente
            url = f"{self.supabase_url}/rest/v1/conversations?sender_id=eq.{sender_id}"
            try:
                response = requests.patch(url, headers=patch_headers, json=update_data)
                response.raise_for_status()
                result = response.json()
                return result[0] if isinstance(result, list) and len(result) > 0 else result
            except requests.exceptions.RequestException as e:
                print(f"Error updating conversation: {e}")
                if hasattr(e, 'response') and hasattr(e.response, 'text'):
                    print(f"Response text: {e.response.text}")
                return {}
            
        except Exception as e:
            print(f"Error adding message to conversation: {e}")
            return {}

    async def get_conversation_history(
        self,
        sender_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtém o histórico de mensagens de uma conversa
        
        Args:
            sender_id: ID do usuário
            limit: Número máximo de mensagens para retornar
        """
        try:
            conversation = await self.get_or_create_conversation(sender_id)
            if not conversation:
                return []
            
            messages = conversation.get("content", {}).get("messages", [])
            
            # Retorna as últimas 'limit' mensagens
            return messages[-limit:] if limit > 0 else messages
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    async def get_conversation_context(
        self,
        sender_id: str
    ) -> Dict[str, Any]:
        """
        Obtém o contexto da conversa
        
        Args:
            sender_id: ID do usuário
        """
        try:
            conversation = await self.get_or_create_conversation(sender_id)
            if not conversation:
                return {}
            
            return conversation.get("content", {}).get("context", {})
            
        except Exception as e:
            print(f"Error getting conversation context: {e}")
            return {}

    async def save_message(
        self,
        source: str,
        sender_id: str,
        original_message: str,
        is_user: bool,
        conversation_id: Optional[str] = None,
        parent_message_id: Optional[str] = None,
        llm_responses: Optional[List[Dict]] = None,
        context: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Save a message to the database with the new JSONB structure
        
        Args:
            source: 'web' or 'whatsapp'
            sender_id: phone number for whatsapp or user id for web
            original_message: the original message text
            is_user: if True, message is from user, if False, from agent
            conversation_id: UUID of the conversation (optional)
            parent_message_id: UUID of the parent message (optional)
            llm_responses: list of responses from different LLMs
            context: contextual information about the message
            metadata: additional metadata
        """
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
            
        content = {
            "original_message": original_message,
            "processed_messages": llm_responses or [],
            "final_response": llm_responses[-1]["response"] if llm_responses else original_message,
            "context": context or {}
        }
        
        data = {
            "source": source,
            "sender_id": sender_id,
            "content": content,
            "is_user": is_user,
            "metadata": metadata or {},
            "conversation_id": conversation_id,
            "parent_message_id": parent_message_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            result = self._make_request("POST", "messages", data)
            return result if result else {}
        except Exception as e:
            print(f"Error saving message to database: {e}")
            return {}

    async def get_chat_history(
        self,
        sender_id: str,
        source: str,
        limit: int = 50,
        conversation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get chat history with the new structure
        
        Args:
            sender_id: phone number or user id
            source: 'web' or 'whatsapp'
            limit: maximum number of messages to return
            conversation_id: optional conversation UUID to filter by
        """
        try:
            filters = [
                f"sender_id=eq.{sender_id}",
                f"source=eq.{source}"
            ]
            
            if conversation_id:
                filters.append(f"conversation_id=eq.{conversation_id}")
                
            endpoint = f"messages?{'.and.'.join(filters)}&order=created_at.asc&limit={limit}"
            result = self._make_request("GET", endpoint)
            return result if result else []
        except Exception as e:
            print(f"Error fetching chat history: {e}")
            return []

    async def update_message_with_llm_response(
        self,
        message_id: str,
        llm_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a message with a new LLM response
        
        Args:
            message_id: UUID of the message to update
            llm_response: dictionary containing the LLM response data
        """
        try:
            # Primeiro busca a mensagem atual
            current = self._make_request("GET", f"messages?id=eq.{message_id}")
            if not current or len(current) == 0:
                print(f"Message {message_id} not found")
                return {}
            
            # Pega o primeiro resultado
            current_message = current[0]
            print("Current message:", current_message)  # Debug log
            
            # Atualiza o content
            content = current_message.get("content", {})
            if not isinstance(content, dict):
                content = {}
            
            # Adiciona a resposta do LLM ao processed_messages
            if "processed_messages" not in content:
                content["processed_messages"] = []
            content["processed_messages"].append(llm_response)
            
            # Atualiza a resposta final
            content["final_response"] = llm_response.get("response", "")
            
            # Prepara os dados para atualização
            update_data = {
                "content": content,
                "metadata": {
                    **(current_message.get("metadata", {}) or {}),
                    "last_llm": llm_response.get("llm"),
                    "last_model": llm_response.get("model"),
                    "last_update": datetime.utcnow().isoformat(),
                    "classification": llm_response.get("classification"),
                    **llm_response.get("metadata", {})
                }
            }
            
            print("Update data:", update_data)  # Debug log
            
            # Atualiza a mensagem usando PUT
            result = self._make_request(
                "PUT", 
                f"messages?id=eq.{message_id}", 
                update_data
            )
            
            print("Update result:", result)  # Debug log
            return result
        
        except Exception as e:
            print(f"Error updating message with LLM response: {e}")
            return {}

    async def save_server_status(self, server_name: str, status: bool, tools: List[str]) -> Dict[str, Any]:
        """
        Save or update server status
        """
        data = {
            "server_name": server_name,
            "is_connected": status,
            "tools": tools,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        try:
            endpoint = f"server_status?on_conflict=server_name"
            result = self._make_request("POST", endpoint, data)
            return result if result else {}
        except Exception as e:
            print(f"Error saving server status: {e}")
            return {}

    async def get_server_statuses(self) -> List[Dict[str, Any]]:
        """
        Get all server statuses
        """
        try:
            result = self._make_request("GET", "server_status")
            return result if result else []
        except Exception as e:
            print(f"Error fetching server statuses: {e}")
            return []

    async def update_conversation(
        self,
        sender_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Atualiza uma conversa existente
        
        Args:
            sender_id: ID do usuário
            update_data: Dados para atualizar
        """
        try:
            # Modifica os headers para usar PATCH
            patch_headers = {**self.headers}
            patch_headers["Prefer"] = "return=representation"
            
            # Faz a requisição PATCH diretamente
            url = f"{self.supabase_url}/rest/v1/conversations?sender_id=eq.{sender_id}"
            try:
                response = requests.patch(url, headers=patch_headers, json=update_data)
                response.raise_for_status()
                result = response.json()
                return result[0] if isinstance(result, list) and len(result) > 0 else result
            except requests.exceptions.RequestException as e:
                print(f"Error updating conversation: {e}")
                if hasattr(e, 'response') and hasattr(e.response, 'text'):
                    print(f"Response text: {e.response.text}")
                return {}
            
        except Exception as e:
            print(f"Error in update_conversation: {e}")
            return {}