from typing import Optional, Dict, Any, List, Tuple
import os
from dotenv import load_dotenv
import anthropic
import requests
import google.generativeai as genai
from .settings import get_settings
from openai import AsyncOpenAI
import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
import json
import asyncio
import aiohttp
from datetime import datetime
from anthropic import AsyncAnthropic

# Configurar rich console e logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

load_dotenv()
settings = get_settings()

class LLMRouter:
    """Router para selecionar o melhor LLM para cada tipo de pergunta"""
    
    def __init__(self):
        # Inicializa clientes dos LLMs
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.gemini = genai.GenerativeModel('gemini-1.5-pro')
        
        # Status dos modelos
        self.models_status: Dict[str, bool] = {
            "openai": True,
            "anthropic": True,
            "gemini": True,
            "deepseek": True
        }
        
        # Timestamp da última verificação
        self.last_check: Dict[str, datetime] = {}

    def log_api_call(self, model: str, prompt_preview: str):
        """Log estilizado de chamada de API"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Model")
        table.add_column("Prompt Preview")
        table.add_column("Timestamp")
        table.add_row(
            f"[cyan]{model}[/cyan]",
            f"[yellow]{prompt_preview[:50]}...[/yellow]",
            f"[green]{datetime.now().strftime('%H:%M:%S')}[/green]"
        )
        console.print(table)

    def log_model_status(self, model_name: str, status: bool, extra_info: str = ""):
        """Log estilizado do status do modelo"""
        status_emoji = "✅" if status else "❌"
        status_color = "green" if status else "red"
        console.print(Panel(
            f"[{status_color}]{status_emoji} {model_name.upper()}[/{status_color}]: {extra_info}",
            border_style=status_color
        ))

    def _update_model_status(self, model_name: str, status: bool):
        """Atualiza o status de um modelo"""
        self.models_status[model_name] = status
        self.last_check[model_name] = datetime.utcnow()
        self.log_model_status(model_name, status)
        
    async def _call_anthropic(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Chama a API Anthropic com o prompt fornecido"""
        try:
            if not self.anthropic:
                raise Exception("Cliente Anthropic não inicializado")
            
            self.log_api_call("Anthropic", prompt)
            
            # Constrói a mensagem com system prompt
            messages = []
            
            # Chama a API Anthropic
            response = await self.anthropic.messages.create(
                model="claude-3-opus",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
                system=system_prompt,  # Passa o system prompt diretamente
                temperature=0.7
            )
            
            self._update_model_status("anthropic", True)
            console.print("[bold green]✓[/bold green] Anthropic response received")
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Erro ao chamar Anthropic: {str(e)}")
            self._update_model_status("anthropic", False)
            
            # Se falhar, tenta usar OpenAI como fallback
            try:
                console.print("[yellow]! Usando OpenAI como fallback para Anthropic[/yellow]")
                return await self._call_openai(prompt, system_prompt)
            except:
                raise Exception(f"Falha ao chamar Anthropic e OpenAI: {str(e)}")
        
    async def _call_gemini(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Chama o Gemini da Google"""
        try:
            self.log_api_call("Gemini", prompt)
            
            # Combina system prompt com o prompt do usuário
            full_prompt = f"{system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
            
            response = await asyncio.to_thread(
                self.gemini.generate_content,
                full_prompt
            )
            self._update_model_status("gemini", True)
            console.print("[bold green]✓[/bold green] Gemini response received")
            return response.text
        except Exception as e:
            logger.error(f"[bold red]✗[/bold red] Erro no Gemini: {str(e)}")
            self._update_model_status("gemini", False)
            raise
        
    async def _call_deepseek(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Chama o DeepSeek"""
        try:
            self.log_api_call("DeepSeek", prompt)
            headers = {
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Prepara as mensagens com system prompt
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    response_json = await response.json()
                    if response.status != 200:
                        raise Exception(f"DeepSeek API error: {response_json}")
                    self._update_model_status("deepseek", True)
                    console.print("[bold green]✓[/bold green] DeepSeek response received")
                    return response_json["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erro no DeepSeek: {str(e)}")
            self._update_model_status("deepseek", False)
            raise

    async def _call_openai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Chama a API OpenAI com o prompt fornecido"""
        try:
            if not self.openai:
                return "Cliente OpenAI não inicializado"
            
            self.log_api_call("OpenAI", prompt)
            
            # Constrói os parâmetros de requisição
            messages = []
            
            # Sempre adiciona o system prompt se fornecido
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Adiciona o prompt do usuário
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Chama a API OpenAI
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=4096,
                temperature=0.7
            )
            
            self._update_model_status("openai", True)
            console.print("[bold green]✓[/bold green] OpenAI response received")
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro ao chamar OpenAI: {str(e)}")
            self._update_model_status("openai", False)
            raise

    def get_available_models(self) -> List[str]:
        """Retorna a lista de modelos disponíveis"""
        return [model for model, status in self.models_status.items() if status]

    def _estimate_tokens(self, text: str) -> int:
        """
        Estima o número de tokens em um texto.
        Usa uma aproximação simples: ~4 caracteres por token
        """
        return len(text) // 4

    async def generate_response(self, prompt: str, context: Optional[str] = None, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Gera uma resposta usando o melhor modelo disponível
        
        Args:
            prompt: Prompt do usuário
            context: Contexto opcional da conversa
            system_prompt: System prompt do agente
            
        Returns:
            Dict com a resposta e metadados
        """
        try:
            # Seleciona o melhor modelo
            selected_model = await self._select_best_model(prompt)
            
            # Combina o contexto com o prompt se fornecido
            full_prompt = f"Contexto: {context}\n\nPergunta: {prompt}" if context else prompt
            
            # Chama o modelo selecionado com o system prompt do agente
            response = await self._call_llm(
                model_name=selected_model,
                prompt=full_prompt,
                system_prompt=system_prompt
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {str(e)}")
            raise

    def _get_model_name(self, llm: str) -> str:
        """Retorna o nome específico do modelo para cada LLM"""
        model_names = {
            "anthropic": "claude-3-opus",
            "openai": "gpt-4",
            "gemini": "gemini-1.5-pro",
            "deepseek": "deepseek-chat",
            "system": "system"
        }
        return model_names.get(llm, "default")

    async def detect_tool_need(self, message: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Detecta se o usuário precisa de uma ferramenta específica e qual ferramenta usar
        
        Returns:
            Tuple[bool, Dict]: (precisa_ferramenta, {tool_name, tool_input, server_name})
        """
        try:
            # Palavras-chave que indicam necessidade de pesquisa web
            web_search_keywords = [
                "pesquise", "procure", "busque", "encontre informações sobre",
                "notícias sobre", "dados atuais", "informações recentes",
                "últimas notícias", "dados estatísticos", "pesquisa sobre"
            ]
            
            # Palavras-chave que indicam execução de código
            code_keywords = [
                "execute", "rode", "compile", "debug", "teste este código",
                "execute este programa", "rode este script"
            ]
            
            # Palavras-chave que indicam que NÃO é necessário usar ferramentas
            no_tool_keywords = [
                "inteligência artificial", "ia", "machine learning", "deep learning",
                "rede neural", "explique", "analise", "compare", "descreva",
                "o que é", "como funciona", "por que", "qual"
            ]
            
            # Se contém palavras-chave que indicam que não precisa de ferramenta, retorna False
            if any(keyword in message.lower() for keyword in no_tool_keywords):
                return False, {}
            
            # Verifica necessidade de pesquisa web
            if any(keyword in message.lower() for keyword in web_search_keywords):
                return True, {
                    "tool_name": "search_web",
                    "tool_input": message,
                    "server_name": "web_search",
                    "reason": "Solicitação explícita de pesquisa ou busca de informações"
                }
            
            # Verifica necessidade de execução de código
            if any(keyword in message.lower() for keyword in code_keywords):
                return True, {
                    "tool_name": "execute_code",
                    "tool_input": message,
                    "server_name": "run_python",
                    "reason": "Solicitação explícita de execução de código"
                }
            
            return False, {}
                
        except Exception as e:
            logger.error(f"Erro ao detectar necessidade de ferramenta: {str(e)}")
            return False, {}
            
    async def _call_anthropic_with_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Chama a API Anthropic com response_format=json"""
        try:
            if not self.anthropic:
                return {}
            
            self.log_api_call("Anthropic JSON", user_prompt)
            
            # Chama a API Anthropic
            response = await self.anthropic.messages.create(
                model="claude-3-opus",
                system=system_prompt,
                max_tokens=1024,
                messages=[{"role": "user", "content": user_prompt}],
                response_format={"type": "json"}
            )
            
            self._update_model_status("anthropic", True)
            console.print("[bold green]✓[/bold green] Anthropic JSON response received")
            
            # Extrai o conteúdo JSON
            import json
            return json.loads(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Erro ao chamar Anthropic com JSON: {str(e)}")
            self._update_model_status("anthropic", False)
            return {}

    async def _call_openai_with_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Chama a API OpenAI com response_format=json_object"""
        try:
            if not self.openai:
                return {}
            
            self.log_api_call("OpenAI JSON", user_prompt)
            
            response = await self.openai.chat.completions.create(
                model="gpt-4o-2024-05-13",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=1024
            )
            
            self._update_model_status("openai", True)
            console.print("[bold green]✓[/bold green] OpenAI JSON response received")
            
            # Extrai o conteúdo JSON
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Erro ao chamar OpenAI com JSON: {str(e)}")
            self._update_model_status("openai", False)
            return {}
            
    async def combine_tool_result(self, original_message: str, tool_name: str, tool_result: str) -> str:
        """
        Combina o resultado de uma ferramenta com uma resposta gerada pelo LLM
        
        Args:
            original_message: Mensagem original do usuário
            tool_name: Nome da ferramenta utilizada
            tool_result: Resultado da execução da ferramenta
            
        Returns:
            Resposta combinada
        """
        try:
            # Usa o modelo Anthropic (ou fallback para OpenAI) para combinar resultados
            model = "anthropic" if self.models_status["anthropic"] else "openai"
            
            system_prompt = """
            Você é um assistente que utiliza resultados de ferramentas para elaborar respostas completas e informativas.
            Com base na mensagem original do usuário e no resultado da ferramenta, forneça uma resposta clara 
            que integre as informações obtidas da ferramenta de maneira natural e útil.
            """
            
            prompt = f"""
            Mensagem original do usuário: {original_message}
            
            Ferramenta utilizada: {tool_name}
            
            Resultado da ferramenta:
            {tool_result}
            
            Por favor, elabore uma resposta completa que incorpore o resultado da ferramenta
            de maneira natural e útil para o usuário.
            """
            
            if model == "anthropic":
                response = await self._call_llm("anthropic", prompt, system_prompt)
            else:
                response = await self._call_llm("openai", prompt, system_prompt)
                
            return response
            
        except Exception as e:
            print(f"Erro ao combinar resultado da ferramenta: {str(e)}")
            return f"Resultado da ferramenta: {tool_result}\n\nDesculpe, não foi possível elaborar uma resposta completa."
    
    async def _call_llm(self, model_name: str, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Chama um LLM específico com um prompt opcional de sistema
        
        Args:
            model_name: Nome do modelo a ser chamado (anthropic, openai, etc)
            prompt: Prompt do usuário
            system_prompt: Prompt de sistema opcional
            
        Returns:
            Dict com a resposta e metadados do modelo
        """
        try:
            # Log da chamada
            self.log_api_call(model_name, prompt)
            
            # Estima tokens do prompt e system prompt
            prompt_tokens = self._estimate_tokens(prompt)
            system_tokens = self._estimate_tokens(system_prompt) if system_prompt else 0
            total_input_tokens = prompt_tokens + system_tokens
            
            # Chama o modelo específico
            if model_name == "anthropic":
                response_text = await self._call_anthropic(prompt, system_prompt)
                model_info = {
                    "llm": "anthropic",
                    "model": "claude-3-opus",
                    "classification": "analytical"
                }
            elif model_name == "openai":
                response_text = await self._call_openai(prompt, system_prompt)
                model_info = {
                    "llm": "openai",
                    "model": "gpt-4",
                    "classification": "general"
                }
            elif model_name == "gemini":
                response_text = await self._call_gemini(prompt, system_prompt)
                model_info = {
                    "llm": "gemini",
                    "model": "gemini-1.5-pro",
                    "classification": "creative"
                }
            elif model_name == "deepseek":
                response_text = await self._call_deepseek(prompt, system_prompt)
                model_info = {
                    "llm": "deepseek",
                    "model": "deepseek-chat",
                    "classification": "technical"
                }
            else:
                raise ValueError(f"Modelo desconhecido: {model_name}")
            
            # Estima tokens da resposta
            response_tokens = self._estimate_tokens(response_text)
            
            # Atualiza o status do modelo
            self._update_model_status(model_name, True)
            
            # Retorna resposta com metadados
            return {
                "response": response_text,
                "llm": model_info["llm"],
                "model": model_info["model"],
                "classification": model_info["classification"],
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "model_name": model_name,
                    "system_prompt_used": bool(system_prompt),
                    "prompt_length": len(prompt),
                    "response_length": len(response_text),
                    "input_tokens": total_input_tokens,
                    "response_tokens": response_tokens,
                    "total_tokens": total_input_tokens + response_tokens,
                    "source": "llm_router"
                }
            }
            
        except Exception as e:
            print(f"Erro ao chamar LLM {model_name}: {str(e)}")
            self._update_model_status(model_name, False)
            return {
                "response": f"Erro ao gerar resposta com {model_name}: {str(e)}",
                "llm": "system",
                "model": "error",
                "classification": "error",
                "metadata": {
                    "error": str(e),
                    "source": "llm_router"
                }
            }
    
    async def _update_models_status(self):
        """Atualiza o status de todos os modelos"""
        # Verifica se é hora de atualizar o status (1 minuto desde a última verificação)
        now = datetime.utcnow()
        
        for model, last_check in self.last_check.items():
            # Se último check foi há mais de 1 minuto, atualiza
            if (now - last_check).total_seconds() > 60:
                try:
                    if model == "openai":
                        await self._check_openai()
                    elif model == "anthropic":
                        await self._check_anthropic()
                    elif model == "gemini":
                        await self._check_gemini()
                    elif model == "deepseek":
                        await self._check_deepseek()
                except Exception as e:
                    logger.error(f"Erro ao verificar status do {model}: {str(e)}")
                    # Marca como indisponível em caso de erro
                    self._update_model_status(model, False)
    
    def _classify_query_complexity(self, query: str) -> str:
        """
        Classifica a pergunta em: simples, complexa, analítica ou criativa
        """
        query_lower = query.lower()
        
        # Palavras que indicam consulta complexa (DeepSeek)
        complex_indicators = [
            "calcule", "resolva", "equação", "matemática", "derivada", "integral",
            "função", "matriz", "teorema", "prova", "demonstre", "otimize",
            "debug", "código", "programa", "algoritmo", "implementação"
        ]
        
        # Palavras que indicam consulta analítica (Anthropic)
        analytical_indicators = [
            "analise", "compare", "avalie", "discuta", "explique",
            "interprete", "examine", "investigue", "por que",
            "qual a diferença", "como funciona", "qual o motivo"
        ]
        
        # Palavras que indicam consulta criativa (Gemini)
        creative_indicators = [
            "crie", "invente", "imagine", "desenvolva", "escreva uma história",
            "componha", "desenhe", "projete", "sugira", "ideias", "brainstorm",
            "design", "arte", "criativo", "inovador", "original"
        ]
        
        # Verifica a presença de indicadores
        if any(ind in query_lower for ind in complex_indicators):
            return "complexa"
        elif any(ind in query_lower for ind in analytical_indicators):
            return "analitica"
        elif any(ind in query_lower for ind in creative_indicators):
            return "criativa"
        else:
            return "simples"

    def log_model_selection(self, query: str, complexity: str, selected_model: str, available_models: List[str]):
        """Log detalhado do processo de seleção do modelo"""
        table = Table(title="[bold magenta]Model Selection Process[/bold magenta]", show_header=True)
        table.add_column("Aspect", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Query", f"[yellow]{query[:50]}...[/yellow]")
        table.add_row("Complexity", complexity)
        table.add_row("Available Models", ", ".join(available_models))
        table.add_row("Selected Model", f"[bold]{selected_model}[/bold]")
        
        console.print(table)
        console.print("\n")

    async def _select_best_model(self, query: str) -> str:
        """
        Seleciona o melhor modelo para responder uma pergunta específica
        """
        # Lista de modelos disponíveis
        available_models = self.get_available_models()
        
        if not available_models:
            raise ValueError("Nenhum modelo disponível")
            
        # Classifica o tipo da pergunta
        query_type = self._classify_query_complexity(query)
        
        console.print(Panel(f"[bold blue]Analisando pergunta:[/bold blue] {query[:100]}...", title="Análise da Query"))
        console.print(f"[bold cyan]Tipo da pergunta:[/bold cyan] {query_type}")
        
        # Seleciona o modelo baseado no tipo da pergunta e disponibilidade
        if query_type == "analitica":
            if "anthropic" in available_models:
                console.print("[bold green]Selecionado Anthropic para pergunta analítica[/bold green]")
                return "anthropic"
            elif "openai" in available_models:
                console.print("[bold yellow]Usando OpenAI como alternativa para pergunta analítica[/bold yellow]")
                return "openai"
                
        elif query_type == "complexa":
            if "deepseek" in available_models:
                console.print("[bold green]Selecionado DeepSeek para pergunta complexa[/bold green]")
                return "deepseek"
            elif "anthropic" in available_models:
                console.print("[bold yellow]Usando Anthropic como alternativa para pergunta complexa[/bold yellow]")
                return "anthropic"
                
        elif query_type == "criativa":
            if "gemini" in available_models:
                console.print("[bold green]Selecionado Gemini para pergunta criativa[/bold green]")
                return "gemini"
            elif "openai" in available_models:
                console.print("[bold yellow]Usando OpenAI como alternativa para pergunta criativa[/bold yellow]")
                return "openai"
                
        # Para perguntas simples ou fallback geral
        if "openai" in available_models:
            console.print("[bold green]Selecionado OpenAI[/bold green]")
            return "openai"
        elif "anthropic" in available_models:
            console.print("[bold yellow]Usando Anthropic como alternativa[/bold yellow]")
            return "anthropic"
        elif "gemini" in available_models:
            console.print("[bold yellow]Usando Gemini como alternativa[/bold yellow]")
            return "gemini"
        elif "deepseek" in available_models:
            console.print("[bold yellow]Usando DeepSeek como alternativa[/bold yellow]")
            return "deepseek"
            
        # Se nenhum modelo preferido estiver disponível, usa o primeiro disponível
        console.print(f"[bold red]Nenhum modelo preferido disponível. Usando {available_models[0]}[/bold red]")
        return available_models[0]

# Instância global do router
llm_router = LLMRouter() 