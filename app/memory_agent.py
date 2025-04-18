from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from enum import Enum
import mistralai
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import uuid
from .settings import get_settings

class TopicType(Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    PERSONAL = "personal"

@dataclass
class ConversationMemory:
    topic: str
    topic_type: TopicType
    last_accessed: datetime
    context: Dict[str, Any]
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    llm_history: List[Dict[str, Any]]

class MemoryAgent:
    def __init__(self, database_client):
        self.db = database_client
        self.cache_duration = timedelta(hours=24)
        self.max_context_messages = 10
        
        # Limites de mensagens
        self.max_messages = 1000  # Limite seguro de mensagens por conversa
        self.max_active_messages = 50  # Mensagens mantidas no contexto ativo
        self.cleanup_threshold = 800  # Quando começar a limpar mensagens antigas
        
        # Tamanhos máximos (em caracteres)
        self.max_message_size = 4000  # ~4KB por mensagem
        self.max_metadata_size = 1000  # ~1KB para metadados
        
        # Inicializa cliente Mistral
        settings = get_settings()
        self.mistral = MistralClient(api_key=settings.MISTRAL_API_KEY)
        
    def _truncate_message(self, message: str) -> str:
        """Trunca mensagem para o tamanho máximo permitido"""
        if len(message) > self.max_message_size:
            return message[:self.max_message_size] + "... (truncado)"
        return message
        
    def _clean_metadata(self, metadata: Dict) -> Dict:
        """Limpa e otimiza metadados"""
        essential_keys = [
            "source", "complexity", "model_name", "selected_model",
            "timestamp", "classification"
        ]
        return {k: metadata[k] for k in essential_keys if k in metadata}
        
    async def _analyze_with_mistral(self, messages: List[Dict[str, Any]], task: str) -> Dict[str, Any]:
        """Usa Mistral para análise de mensagens"""
        try:
            # Prepara as mensagens para análise
            formatted_messages = "\n".join([
                f"{'User' if msg['is_user'] else 'Assistant'}: {msg['message']}"
                for msg in messages
            ])
            
            # Define o prompt baseado na tarefa
            if task == "topic":
                prompt = f"""
                Analise as mensagens abaixo e extraia o tópico principal e subtópicos.
                Classifique o tipo de conversa (GENERAL, TECHNICAL, CREATIVE, ANALYTICAL, PERSONAL).
                Retorne em formato JSON com: topic, type, subtopics.

                Mensagens:
                {formatted_messages}
                """
            elif task == "summary":
                prompt = f"""
                Crie um resumo conciso das mensagens abaixo, identificando pontos-chave.
                Retorne em formato JSON com: summary, key_points, sentiment.

                Mensagens:
                {formatted_messages}
                """
            
            try:
                # Chama a API do Mistral
                chat_messages = [
                    ChatMessage(role="system", content="Você é um analisador de contexto especializado em extrair informações relevantes de conversas."),
                    ChatMessage(role="user", content=prompt)
                ]
                
                response = await self.mistral.chat(
                    model="mistral-large-latest",
                    messages=chat_messages
                )
                
                # Processa a resposta
                try:
                    result = json.loads(response.choices[0].message.content)
                    return result
                except json.JSONDecodeError:
                    print("Failed to parse Mistral response, using fallback")
                    return self._get_fallback_analysis(task)
                    
            except Exception as e:
                print(f"Mistral API error: {e}, using fallback")
                return self._get_fallback_analysis(task)
                
        except Exception as e:
            print(f"Error in Mistral analysis: {e}")
            return self._get_fallback_analysis(task)
            
    def _get_fallback_analysis(self, task: str) -> Dict[str, Any]:
        """Fornece análise fallback quando Mistral falha"""
        if task == "topic":
            return {
                "type": TopicType.GENERAL.value,
                "topic": "General conversation",
                "subtopics": [],
                "last_update": datetime.utcnow().isoformat()
            }
        elif task == "summary":
            return {
                "summary": "",
                "key_points": [],
                "sentiment": "neutral",
                "timestamp": datetime.utcnow().isoformat()
            }
        return {}
    
    async def _extract_topic(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrai o tópico atual baseado nas últimas mensagens usando Mistral"""
        if not messages:
            return {"type": TopicType.GENERAL.value, "summary": "No messages"}
            
        # Analisa com Mistral
        analysis = await self._analyze_with_mistral(messages, "topic")
        
        if "error" in analysis:
            return {
                "type": TopicType.GENERAL.value,
                "summary": "General conversation",
                "last_update": datetime.utcnow().isoformat()
            }
            
        return {
            "type": analysis.get("type", TopicType.GENERAL.value),
            "summary": analysis.get("topic", "General conversation"),
            "subtopics": analysis.get("subtopics", []),
            "last_update": datetime.utcnow().isoformat()
        }
    
    def _get_llm_preferences(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Determina as preferências de LLM baseado no histórico"""
        llm_history = content.get("llm_history", [])
        if not llm_history:
            return {}
            
        # Analisa últimos LLMs usados e seus resultados
        return {
            "preferred_llm": llm_history[-1].get("llm"),
            "preferred_model": llm_history[-1].get("model"),
            "last_classification": llm_history[-1].get("classification")
        }
    
    async def _extract_topics_summary(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Gera um resumo dos tópicos discutidos usando Mistral"""
        if not messages:
            return []
            
        # Analisa com Mistral
        analysis = await self._analyze_with_mistral(messages, "summary")
        
        if "error" in analysis:
            return []
            
        return {
            "summary": analysis.get("summary", ""),
            "key_points": analysis.get("key_points", []),
            "sentiment": analysis.get("sentiment", "neutral"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _count_context_switches(self, llm_history: List[Dict[str, Any]]) -> int:
        """Conta quantas vezes houve troca de contexto/LLM"""
        if not llm_history:
            return 0
            
        switches = 0
        last_llm = None
        for entry in llm_history:
            current_llm = entry.get("llm")
            if last_llm and current_llm != last_llm:
                switches += 1
            last_llm = current_llm
        return switches
    
    def _clean_old_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove mensagens mais antigas que 24h"""
        cutoff = datetime.utcnow() - self.cache_duration
        return [
            msg for msg in messages
            if datetime.fromisoformat(msg["timestamp"]) > cutoff
        ]
    
    async def process_message(
        self,
        sender_id: str,
        message: str,
        is_user: bool,
        llm_response: Optional[Dict] = None,
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Processa uma nova mensagem e atualiza o contexto"""
        # Gera um ID único para a mensagem se não fornecido
        if not message_id:
            message_id = str(uuid.uuid4())
            
        # Trunca a mensagem se necessário
        message = self._truncate_message(message)
        
        # Prepara o objeto base da mensagem
        message_obj = {
            "id": message_id,
            "is_user": is_user,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Adiciona informações do LLM se disponível
        if llm_response and not is_user:
            message_obj.update({
                "llm": llm_response.get("llm"),
                "model": llm_response.get("model"),
                "metadata": self._clean_metadata(llm_response.get("metadata", {})),
                "classification": llm_response.get("classification")
            })
            
        # Busca conversa existente ou cria nova
        conversation = await self.db.get_or_create_conversation(sender_id)
        
        # Verifica se a mensagem já existe
        existing_messages = conversation.get("messages", [])
        if any(msg.get("id") == message_id for msg in existing_messages):
            # Retorna a conversa sem modificar se a mensagem já existe
            return conversation
            
        # Atualiza a lista de mensagens
        messages = conversation.get("messages", [])
        messages.append(message_obj)
        
        # Atualiza mensagens ativas
        active_messages = conversation.get("context", {}).get("active_messages", [])
        active_messages.append(message_obj)
        
        # Limita mensagens ativas ao máximo definido
        if len(active_messages) > self.max_active_messages:
            active_messages = active_messages[-self.max_active_messages:]
            
        # Atualiza o tópico ativo
        active_topic = await self._extract_topic(active_messages)
        
        # Atualiza análise de tópicos
        topic_analysis = await self._extract_topics_summary(active_messages)
        
        # Atualiza histórico de LLM se aplicável
        llm_history = conversation.get("llm_history", [])
        if llm_response and not is_user:
            llm_entry = {
                "llm": llm_response.get("llm"),
                "model": llm_response.get("model"),
                "timestamp": datetime.utcnow().isoformat(),
                "classification": llm_response.get("classification")
            }
            llm_history.append(llm_entry)
            
        # Atualiza metadados
        metadata = conversation.get("metadata", {})
        metadata.update({
            "last_update": datetime.utcnow().isoformat(),
            "message_count": len(messages),
            "total_cleaned": metadata.get("total_cleaned", 0),
            "context_switches": self._count_context_switches(llm_history)
        })
        
        # Constrói o contexto atualizado
        context = {
            "active_topic": active_topic,
            "last_accessed": datetime.utcnow().isoformat(),
            "topic_analysis": topic_analysis,
            "active_messages": active_messages,
            "llm_preferences": self._get_llm_preferences({
                "llm_history": llm_history
            })
        }
        
        # Limpa mensagens antigas se necessário
        if len(messages) > self.cleanup_threshold:
            messages = self._clean_old_messages(messages)
            metadata["total_cleaned"] = metadata.get("total_cleaned", 0) + 1
            
        # Salva a mensagem no banco de dados
        await self.db.add_message_to_conversation(
            sender_id=sender_id,
            message=message,
            is_user=is_user,
            llm_response=llm_response
        )
        
        # Retorna a conversa atualizada
        return {
            "context": context,
            "messages": messages,
            "metadata": metadata,
            "llm_history": llm_history
        }
    
    async def get_relevant_context(
        self,
        sender_id: str,
        current_message: str
    ) -> Dict[str, Any]:
        """
        Recupera contexto relevante para a mensagem atual
        """
        try:
            conversation = await self.db.get_or_create_conversation(sender_id)
            if not conversation:
                return {}
                
            content = conversation.get("content", {})
            context = content.get("context", {})
            
            # Retorna contexto ativo
            return {
                "active_topic": context.get("active_topic", {}),
                "active_messages": context.get("active_messages", []),
                "llm_preferences": context.get("llm_preferences", {}),
                "metadata": content.get("metadata", {})
            }
            
        except Exception as e:
            print(f"Error getting relevant context: {e}")
            return {} 