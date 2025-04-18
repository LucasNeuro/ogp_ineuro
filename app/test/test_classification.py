from app.llm_router import LLMRouter
import asyncio
import sys
import os
import pytest

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

@pytest.mark.asyncio
async def test_classification():
    router = LLMRouter()
    
    # Lista de perguntas para teste
    perguntas = [
        # Perguntas Simples
        "Qual é a capital do Brasil?",
        "Me diga o nome do atual presidente dos EUA",
        "Quantos planetas existem no sistema solar?",
        
        # Perguntas Complexas (DeepSeek)
        "Resolva a equação quadrática: 2x² + 5x - 3 = 0",
        "Implemente um algoritmo de ordenação em Python",
        "Calcule a derivada de f(x) = x³ + 2x² - 5x + 1",
        
        # Perguntas Analíticas (Anthropic)
        "Analise o impacto da inteligência artificial na sociedade moderna",
        "Compare os diferentes sistemas econômicos e suas características",
        "Explique por que o céu é azul usando conceitos de física",
        
        # Perguntas Criativas (Gemini)
        "Crie uma história curta sobre um robô que aprende a sentir emoções",
        "Desenhe um conceito para uma casa futurista",
        "Sugira ideias inovadoras para um aplicativo de educação"
    ]
    
    print("\n=== TESTE DO SISTEMA DE CLASSIFICAÇÃO ===\n")
    
    for pergunta in perguntas:
        print(f"\nPergunta: {pergunta}")
        tipo = router._classify_query_complexity(pergunta)
        modelo = await router._select_best_model(pergunta)
        print(f"Classificação: {tipo}")
        print(f"Modelo selecionado: {modelo}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_classification()) 