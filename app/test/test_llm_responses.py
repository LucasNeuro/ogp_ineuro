import asyncio
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import datetime

# Adiciona o diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import ineuro_agent
from app.llm_router import llm_router

console = Console()

async def test_model_responses():
    """Testa as respostas de cada modelo com a mesma pergunta"""
    
    # Pergunta de teste que envolve criatividade e técnica
    test_question = """Desenhe um conceito para uma casa futurista que seja autossustentável 
    e integrada com tecnologia. Inclua aspectos de energia renovável e automação."""
    
    # Lista de modelos para testar
    models = ["claude-3-opus", "gpt-4", "gemini-1.5-pro", "deepseek-chat"]
    
    console.print("\n[bold magenta]🧪 Iniciando testes de resposta dos modelos[/bold magenta]\n")
    
    for model in models:
        try:
            console.print(f"\n[bold blue]Testing {model}[/bold blue]")
            console.print("-" * 80)
            
            # Identifica o tipo de tarefa
            task_type = await ineuro_agent._get_task_type(test_question)
            console.print(f"Task Type: [green]{task_type}[/green]")
            
            # Formata o system prompt para o modelo específico
            system_prompt = await ineuro_agent._format_system_prompt(model, task_type)
            
            # Mostra o prompt formatado
            console.print(Panel(
                system_prompt,
                title="[yellow]System Prompt Formatado[/yellow]",
                expand=False
            ))
            
            # Gera a resposta
            start_time = datetime.now()
            
            response = await llm_router._call_llm(
                model_name=model,
                prompt=test_question,
                system_prompt=system_prompt
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Extrai a resposta e metadados
            response_text = response.get("response", "")
            metadata = response.get("metadata", {})
            
            # Mostra os resultados
            results_table = Table(show_header=True, header_style="bold magenta")
            results_table.add_column("Métrica")
            results_table.add_column("Valor")
            
            results_table.add_row(
                "Tempo de Resposta",
                f"{duration:.2f} segundos"
            )
            results_table.add_row(
                "Tokens Entrada",
                str(metadata.get("input_tokens", "N/A"))
            )
            results_table.add_row(
                "Tokens Resposta",
                str(metadata.get("response_tokens", "N/A"))
            )
            results_table.add_row(
                "Tokens Total",
                str(metadata.get("total_tokens", "N/A"))
            )
            
            console.print(results_table)
            
            # Mostra a resposta formatada
            console.print(Panel(
                response_text,
                title=f"[green]Resposta do {model}[/green]",
                expand=False
            ))
            
        except Exception as e:
            console.print(f"[bold red]Erro ao testar {model}: {str(e)}[/bold red]")
            continue

async def main():
    """Função principal para executar os testes"""
    console.print("[bold]🤖 I-Neuro LLM Response Test[/bold]")
    console.print("Testando respostas dos diferentes modelos...")
    
    await test_model_responses()

if __name__ == "__main__":
    asyncio.run(main()) 