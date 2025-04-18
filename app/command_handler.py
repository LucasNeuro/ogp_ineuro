from typing import Dict, Any, Optional
from enum import Enum
import json

class CommandType(Enum):
    BASE = "/base"
    PERSONA = "/persona"
    PROMPT = "/prompt"
    HELP = "/help"
    NONE = ""

class InteractiveCard:
    def __init__(self, command_type: CommandType):
        self.command_type = command_type
        
    def to_dict(self) -> Dict[str, Any]:
        """Converte o card para dicionário"""
        base_card = {
            "type": "interactive_card",
            "command_type": self.command_type.name,
            "command": self.command_type.value,
            "show": True
        }
        
        if self.command_type == CommandType.BASE:
            base_card.update({
                "title": "Upload de Base de Conhecimento",
                "components": [
                    {
                        "type": "file_upload",
                        "id": "base_files",
                        "label": "Arraste os arquivos aqui ou clique para selecionar",
                        "accept": "*/*",
                        "multiple": True
                    },
                    {
                        "type": "file_list",
                        "id": "selected_files",
                        "label": "Arquivos Selecionados"
                    },
                    {
                        "type": "button",
                        "id": "upload_button",
                        "label": "Fazer Upload",
                        "action": "upload_base",
                        "icon": "fa-upload"
                    }
                ]
            })
            
        elif self.command_type == CommandType.PERSONA:
            base_card.update({
                "title": "Configurar Personalidade",
                "components": [
                    {
                        "type": "text_input",
                        "id": "persona_description",
                        "label": "Descreva a personalidade desejada",
                        "placeholder": "Ex: Um assistente amigável e informal que usa emojis..."
                    },
                    {
                        "type": "dropdown",
                        "id": "persona_type",
                        "label": "Ou selecione um tipo pré-definido",
                        "default_value": "friendly",
                        "options": [
                            {"value": "friendly", "label": "Amigável"},
                            {"value": "professional", "label": "Profissional"},
                            {"value": "charismatic", "label": "Carismático"},
                            {"value": "technical", "label": "Técnico"}
                        ]
                    },
                    {
                        "type": "button",
                        "id": "save_persona",
                        "label": "Salvar Personalidade",
                        "action": "save_persona",
                        "icon": "fa-save"
                    }
                ]
            })
            
        elif self.command_type == CommandType.PROMPT:
            base_card.update({
                "title": "Upload de Prompt",
                "components": [
                    {
                        "type": "file_upload",
                        "id": "prompt_file",
                        "label": "Selecione o arquivo markdown",
                        "accept": ".md",
                        "multiple": False
                    },
                    {
                        "type": "text_preview",
                        "id": "prompt_preview",
                        "label": "Visualização do Prompt"
                    },
                    {
                        "type": "button",
                        "id": "save_prompt",
                        "label": "Salvar Prompt",
                        "action": "save_prompt",
                        "icon": "fa-save"
                    }
                ]
            })
            
        elif self.command_type == CommandType.HELP:
            base_card.update({
                "title": "Ajuda - Comandos Disponíveis",
                "components": [
                    {
                        "type": "text_preview",
                        "id": "help_content",
                        "label": "Comandos disponíveis",
                        "default_value": """
/base - Carregar uma base de conhecimento (documentos, PDFs, etc)
/persona - Configurar a personalidade do assistente
/prompt - Configurar o prompt base do sistema
/help - Mostrar esta mensagem de ajuda
                        """
                    },
                    {
                        "type": "button",
                        "id": "close_help",
                        "label": "Fechar",
                        "action": "close",
                        "icon": "fa-times"
                    }
                ]
            })
            
        return base_card

class CommandHandler:
    def __init__(self):
        self.commands = {
            CommandType.BASE.value: self._handle_base_command,
            CommandType.PERSONA.value: self._handle_persona_command,
            CommandType.PROMPT.value: self._handle_prompt_command,
            CommandType.HELP.value: self._handle_help_command
        }
    
    def is_command(self, message: str) -> bool:
        """Verifica se a mensagem é um comando"""
        return message.strip().startswith("/")
    
    def get_command_type(self, message: str) -> CommandType:
        """Retorna o tipo do comando ou NONE se não for um comando válido"""
        message = message.strip().lower()
        for command_type in CommandType:
            if message.startswith(command_type.value):
                return command_type
        return CommandType.NONE
    
    async def handle_command(self, message: str) -> Dict[str, Any]:
        """Processa um comando e retorna a resposta apropriada"""
        command_type = self.get_command_type(message)
        
        if command_type == CommandType.NONE:
            return {
                "response": "Comando inválido",
                "model": "system",
                "error": True
            }
            
        # Cria e retorna o card interativo apropriado
        card = InteractiveCard(command_type)
        return card.to_dict()
    
    async def _handle_base_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa o comando /base"""
        if not data.get("files"):
            return {
                "response": "Erro: Nenhum arquivo foi fornecido",
                "model": "system",
                "error": True
            }
            
        # Aqui você implementaria o processamento dos arquivos
        # Por exemplo, enviar para um serviço de embeddings, salvar metadados no banco, etc.
        
        # Simulando o processamento
        num_files = len(data.get("files", []))
        file_names = ", ".join(data.get("files", [])[:3])
        if num_files > 3:
            file_names += f" e mais {num_files - 3} arquivo(s)"
            
        return {
            "response": f"Base de conhecimento atualizada com sucesso! Arquivos processados: {file_names}",
            "model": "system"
        }
    
    async def _handle_persona_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa o comando /persona"""
        description = data.get("description", "")
        persona_type = data.get("type", "")
        
        if not description and not persona_type:
            return {
                "response": "Erro: É necessário fornecer uma descrição ou selecionar um tipo de persona",
                "model": "system",
                "error": True
            }
            
        # Aqui você implementaria a lógica para salvar a persona no sistema
        # Por exemplo, atualizar um arquivo de configuração, banco de dados, etc.
        
        # Templates pré-definidos para personalidades
        persona_templates = {
            "friendly": "Assistente amigável e conversacional que usa linguagem informal e emojis ocasionais",
            "professional": "Assistente formal e profissional com respostas objetivas e precisas",
            "charismatic": "Assistente carismático e envolvente que mantém a conversa interessante",
            "technical": "Assistente técnico detalhado que fornece informações precisas e aprofundadas"
        }
        
        if persona_type and not description:
            description = persona_templates.get(persona_type, "")
            
        # Simulando o processamento
        response_message = f"Personalidade configurada com sucesso!"
        if persona_type:
            response_message += f" Tipo: {persona_type.capitalize()}"
        if description:
            short_desc = description[:50] + "..." if len(description) > 50 else description
            response_message += f" Descrição: {short_desc}"
            
        return {
            "response": response_message,
            "model": "system"
        }
    
    async def _handle_prompt_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa o comando /prompt"""
        prompt = data.get("prompt", "")
        
        if not prompt:
            return {
                "response": "Erro: É necessário fornecer um prompt",
                "model": "system",
                "error": True
            }
            
        # Aqui você implementaria a lógica para salvar o prompt base no sistema
        # Por exemplo, atualizar um arquivo de configuração, banco de dados, etc.
        
        # Simulando o processamento
        short_prompt = prompt[:50] + "..." if len(prompt) > 50 else prompt
        
        return {
            "response": f"Prompt base atualizado com sucesso! Prompt: {short_prompt}",
            "model": "system"
        }
    
    async def _handle_help_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa o comando /help"""
        help_text = """
**Comandos disponíveis:**

- **/base** - Carregar uma base de conhecimento (documentos, PDFs, etc)
- **/persona** - Configurar a personalidade do assistente
- **/prompt** - Configurar o prompt base do sistema
- **/help** - Mostrar esta mensagem de ajuda
        """
        
        return {
            "response": help_text,
            "model": "system"
        }

# Instância global do handler
command_handler = CommandHandler() 