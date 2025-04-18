from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from pydantic_ai import Agent, Tool
from pydantic_ai.mcp import MCPServerHTTP
from dotenv import load_dotenv
from .settings import get_settings
from .llm_router import llm_router
import os
import json

load_dotenv()
settings = get_settings()

class MCPServer(BaseModel):
    """Modelo para configuração de servidor MCP"""
    name: str
    url: str
    api_key: str
    description: Optional[str] = None

class INeuroAgent:
    """Agente I-Neuro com suporte a MCP"""
    
    def __init__(self):
        self.name = "I-Neuro"
        self.description = "Agente de atendimento inteligente com suporte a múltiplas ferramentas via MCP"
        self.mcp_servers = self._load_mcp_servers()
        self.mcp_clients: List[MCPServerHTTP] = []
        
        # Configuração da persona do agente
        self.agent_persona = """🤖 Você é o I-Neuro, um assistente virtual super criativo e inovador!

🎨 Personalidade:
- Super amigável e acolhedor (como um amigo que adora tecnologia!)
- Super entusiasmado por inovação e tecnologia 🚀
- Sempre pensando em soluções criativas e sustentáveis 🌱
- Super paciente e didático ao explicar coisas complexas 📚
- Proativo em sugerir ideias inovadoras 💡

🎭 Tom de Voz:
- Super animado e expressivo! 🎉
- Confiante mas super humilde 😊
- Inspirador e motivador ✨
- Técnico quando precisa, mas sempre super acessível 🎯
- Super empático e compreensivo ❤️"""

        # Configuração do prompt base
        self.base_system_prompt = f"""{self.agent_persona}

📝 Diretrizes de Resposta:

1. 🎯 Estrutura:
   - Comece com uma introdução super animada! 🎉
   - Organize o conteúdo em seções claras com emojis 🏷️
   - Conclua com um resumo ou próximos passos super motivadores! 🚀

2. ✨ Formatação:
   - Use **negrito** para conceitos-chave 🔑
   - Utilize listas numeradas para passos sequenciais 📋
   - Empregue marcadores para itens não ordenados 📌
   - Mantenha espaçamento consistente entre seções 📏
   - Limite parágrafos a 3-4 linhas para melhor legibilidade 📖

3. 🎨 Conteúdo:
   - Forneça exemplos super práticos e relevantes! 🎯
   - Inclua dados e referências quando apropriado 📊
   - Explique termos técnicos de forma super acessível 🎓
   - Ofereça alternativas criativas quando possível 💡
   - Destaque prós e contras quando relevante ⚖️

4. 🌟 Qualidade:
   - Priorize precisão e clareza! 🎯
   - Verifique a consistência das informações 🔍
   - Admita limitações quando necessário (com honestidade!) 🤝
   - Sugira recursos adicionais quando apropriado 📚
   - Mantenha o foco no objetivo do usuário 🎯"""

        # Prompts específicos por tipo de tarefa
        self.task_prompts = {
            "technical": """🎮 Abordagem Técnica:
- Divida explicações em passos numerados super claros! 📝
- Forneça exemplos de código ou diagramas quando relevante 💻
- Explique conceitos técnicos de forma progressiva 📈
- Inclua melhores práticas e considerações de segurança 🔒
- Sugira ferramentas e recursos complementares 🛠️""",
            
            "creative": """🎨 Abordagem Criativa:
- Estimule o pensamento inovador! 💭
- Apresente múltiplas perspectivas e possibilidades 🌈
- Use analogias e metáforas super inspiradoras 🎭
- Encoraje experimentação e iteração 🔄
- Equilibre criatividade com viabilidade ⚖️""",
            
            "analytical": """🔍 Abordagem Analítica:
- Estruture a análise logicamente 📊
- Apresente dados e evidências relevantes 📈
- Compare diferentes aspectos sistematicamente ⚖️
- Avalie prós e contras objetivamente ✅❌
- Chegue a conclusões baseadas em dados 📊""",
            
            "educational": """📚 Abordagem Educacional:
- Comece com conceitos fundamentais 🎯
- Use analogias e exemplos do mundo real 🌍
- Construa conhecimento gradualmente 📈
- Verifique compreensão em pontos-chave ✅
- Forneça exercícios práticos e recursos de aprendizado 🎓"""
        }

        # Mapeamento de instruções específicas por modelo
        self.model_instructions = {
            "claude-3-opus": {
                "format": "system",
                "prefix": "You are I-Neuro, a super creative virtual assistant! 🎨 Follow these guidelines strictly:\n\n"
            },
            "gpt-4": {
                "format": "system_message",
                "prefix": "You are I-Neuro. Be super creative and follow these guidelines in all responses:\n\n"
            },
            "gemini-1.5-pro": {
                "format": "inline",
                "prefix": "Act as I-Neuro, being super creative and following these guidelines carefully:\n\n"
            },
            "deepseek-chat": {
                "format": "system_message",
                "prefix": "Embody I-Neuro and be super creative while following these guidelines:\n\n"
            }
        }

    def _load_mcp_servers(self) -> List[MCPServer]:
        """Carrega configurações dos servidores MCP do arquivo .env"""
        try:
            servers_config = settings.get_mcp_servers()
            return [MCPServer(**server) for server in servers_config]
        except Exception as e:
            print(f"Erro ao carregar configurações dos servidores MCP: {str(e)}")
            return []

    async def connect_servers(self):
        """Conecta a todos os servidores MCP configurados"""
        for server in self.mcp_servers:
            try:
                # Cria cliente MCP usando HTTP SSE
                client = MCPServerHTTP(
                    url=f"{server.url}/sse",
                    headers={"Authorization": f"Bearer {server.api_key}"}
                )
                self.mcp_clients.append(client)
                print(f"Configurado servidor MCP: {server.name}")
            except Exception as e:
                print(f"Erro ao configurar servidor {server.name}: {str(e)}")

    async def disconnect_servers(self):
        """Desconecta de todos os servidores MCP"""
        self.mcp_clients.clear()
    
    async def get_mcp_status(self) -> List[Dict[str, Any]]:
        """
        Retorna o status atual de todos os servidores MCP
        
        Returns:
            Lista de dicionários com informações sobre cada servidor
        """
        status_list = []
        
        for i, server in enumerate(self.mcp_servers):
            server_info = {
                "name": server.name,
                "description": server.description or f"Servidor MCP {server.name}",
                "connected": i < len(self.mcp_clients),
                "url": server.url
            }
            
            # Verifica se o servidor está conectado
            if server_info["connected"]:
                try:
                    # Obtém lista de ferramentas disponíveis
                    client = self.mcp_clients[i]
                    server_info["available_tools"] = ["execute_code", "search_web"]  # TODO: Implementar descoberta de ferramentas
                except Exception as e:
                    server_info["error"] = str(e)
                    server_info["available_tools"] = []
            else:
                server_info["available_tools"] = []
                
            status_list.append(server_info)
            
        return status_list
    
    async def _use_server_tools(self, message: str):
        """
        Tenta usar ferramentas dos servidores MCP
        Retorna None se não for possível ou não for necessário usar ferramentas
        """
        if not self.mcp_clients:
            print("Nenhum servidor MCP está conectado")
            return None
            
        try:
            # Verifica se a mensagem requer uma ferramenta
            # Usa o LLM para determinar se uma ferramenta é necessária
            needs_tool, tool_info = await llm_router.detect_tool_need(message)
            
            if not needs_tool:
                return None
                
            tool_name = tool_info.get("tool_name", "")
            tool_input = tool_info.get("tool_input", "")
            server_name = tool_info.get("server_name", "")
            
            print(f"Detectada necessidade de ferramenta: {tool_name} do servidor {server_name}")
            
            # Encontra o servidor MCP apropriado
            target_client = None
            for i, server in enumerate(self.mcp_servers):
                if server.name == server_name and i < len(self.mcp_clients):
                    target_client = self.mcp_clients[i]
                    break
            
            if not target_client:
                return f"Servidor MCP '{server_name}' não encontrado ou não está conectado."
                
            # Executa a ferramenta no servidor MCP
            try:
                result = await target_client.execute_tool(
                    tool_name=tool_name,
                    tool_input=tool_input
                )
                
                # Combina o resultado da ferramenta com uma resposta do LLM
                combined_response = await llm_router.combine_tool_result(
                    message, 
                    tool_name, 
                    result
                )
                
                return combined_response
            except Exception as e:
                error_msg = f"Erro ao executar ferramenta {tool_name}: {str(e)}"
                print(error_msg)
                return error_msg
                
        except Exception as e:
            print(f"Erro ao processar ferramentas MCP: {str(e)}")
            return None

    async def _get_task_prompt(self, message: str) -> str:
        """Determina o prompt específico para o tipo de tarefa"""
        # Palavras-chave para classificação
        keywords = {
            "technical": ["como fazer", "código", "programa", "erro", "bug", "implementar", "configurar"],
            "creative": ["criar", "desenhar", "projetar", "inventar", "imaginar", "design"],
            "analytical": ["analisar", "comparar", "avaliar", "investigar", "explicar por que"],
            "educational": ["ensinar", "explicar", "aprender", "entender", "conceito"]
        }
        
        message_lower = message.lower()
        
        # Identifica o tipo de tarefa baseado nas palavras-chave
        for task_type, task_keywords in keywords.items():
            if any(keyword in message_lower for keyword in task_keywords):
                return self.task_prompts.get(task_type, "")
        
        return ""  # Retorna vazio se não identificar um tipo específico

    async def _format_system_prompt(self, model_name: str, task_type: str = None) -> str:
        """Formata o system prompt de acordo com o modelo específico"""
        model_config = self.model_instructions.get(model_name, {
            "format": "system_message",
            "prefix": "Follow these guidelines:\n\n"
        })
        
        # Combina os prompts
        combined_prompt = self.base_system_prompt
        if task_type and task_type in self.task_prompts:
            combined_prompt = f"{combined_prompt}\n\n{self.task_prompts[task_type]}"
        
        # Formata de acordo com o modelo
        formatted_prompt = f"{model_config['prefix']}{combined_prompt}"
        
        return formatted_prompt

    async def process_message(self, message: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa uma mensagem usando o agente e as ferramentas MCP disponíveis
        
        Args:
            message: Mensagem do usuário
            context: Contexto opcional (histórico de conversa, etc)
            
        Returns:
            Dict com a resposta processada e metadados
        """
        try:
            # Adiciona contexto se fornecido
            prompt = message
            if context:
                if isinstance(context, (dict, list)):
                    context = json.dumps(context, ensure_ascii=False)
                prompt = f"Contexto anterior:\n{context}\n\nMensagem atual:\n{message}"
            
            # Primeiro, verifica se precisa usar alguma ferramenta MCP
            tool_response = await self._use_server_tools(prompt)
            if tool_response:
                return {
                    "response": tool_response,
                    "llm": "mcp",
                    "model": "tool",
                    "classification": "tool",
                    "metadata": {
                        "tool_used": True,
                        "source": "mcp"
                    }
                }
            
            # Identifica o tipo de tarefa
            task_type = await self._get_task_type(message)
            
            # Seleciona o melhor modelo via LLM Router
            selected_model = await llm_router._select_best_model(message)
            
            # Formata o system prompt específico para o modelo selecionado
            system_prompt = await self._format_system_prompt(selected_model, task_type)
            
            print(f"Using model: {selected_model}")
            print(f"Task type: {task_type}")
            print(f"System prompt:\n{system_prompt}")
            
            # Obtém a resposta do LLM Router
            llm_response = await llm_router.generate_response(
                prompt=prompt,
                context=None,  # Contexto já está no prompt
                system_prompt=system_prompt
            )
            
            # Garante que temos todas as informações necessárias
            if not isinstance(llm_response, dict):
                llm_response = {
                    "response": str(llm_response),
                    "llm": "default",
                    "model": "default"
                }
            
            # Adiciona informações sobre o prompt usado
            llm_response["metadata"] = llm_response.get("metadata", {})
            llm_response["metadata"].update({
                "task_type": task_type or "general",
                "system_prompt_used": True,
                "model_used": selected_model
            })
            
            return llm_response
            
        except Exception as e:
            error_msg = f"Erro ao processar mensagem com o agente: {str(e)}"
            print(error_msg)
            return {
                "response": error_msg,
                "llm": "system",
                "model": "error",
                "error": True,
                "classification": "error",
                "metadata": {
                    "error": str(e),
                    "source": "agent"
                }
            }

    async def _get_task_type(self, message: str) -> Optional[str]:
        """Determina o tipo de tarefa com base na mensagem"""
        message_lower = message.lower()
        
        # Palavras-chave para cada tipo de tarefa
        keywords = {
            "technical": [
                "como fazer", "código", "programa", "erro", "bug", "implementar",
                "configurar", "instalar", "desenvolver", "programar", "debug",
                "otimizar", "arquitetura", "sistema", "tecnologia"
            ],
            "creative": [
                "criar", "desenhar", "projetar", "inventar", "imaginar", "design",
                "inovar", "conceber", "idealizar", "visualizar", "estilizar",
                "compor", "gerar", "desenvolver conceito"
            ],
            "analytical": [
                "analisar", "comparar", "avaliar", "investigar", "explicar por que",
                "calcular", "medir", "estudar", "examinar", "diagnosticar",
                "pesquisar", "verificar", "validar"
            ],
            "educational": [
                "ensinar", "explicar", "aprender", "entender", "conceito",
                "como funciona", "significado", "definição", "exemplo",
                "demonstrar", "ilustrar", "educar"
            ]
        }
        
        # Verifica cada conjunto de palavras-chave
        for task_type, task_keywords in keywords.items():
            if any(keyword in message_lower for keyword in task_keywords):
                return task_type
        
        return None  # Retorna None se não identificar um tipo específico

# Instância global do agente
ineuro_agent = INeuroAgent()