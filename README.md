# I-Neuro: Assistente Virtual Inteligente

Um assistente virtual avançado que combina múltiplos modelos de linguagem (LLMs) com uma interface web moderna e integração com WhatsApp.

## 🚀 Funcionalidades

- **Multi-LLM**: Suporte a diversos modelos (Claude, GPT-4, Gemini, DeepSeek)
- **Interface Web Moderna**: Design system próprio com UI/UX otimizada
- **Integração WhatsApp**: Comunicação direta via WhatsApp
- **Base de Conhecimento**: Sistema para gestão de documentos e contexto
- **Memória Persistente**: Armazenamento de conversas e contextos
- **Personalização**: Sistema de prompts e personalidades customizáveis

## 📦 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/LucasNeuro/ogp_ineuro.git
cd ogp_ineuro
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
- Copie `.env.example` para `.env`
- Configure as chaves de API:
  - Anthropic (Claude)
  - OpenAI (GPT-4)
  - Google (Gemini)
  - DeepSeek
  - WhatsApp Business API

## 🏃‍♂️ Executando

1. Inicie o servidor:
```bash
python run.py
```

2. Acesse a interface web:
```
http://localhost:5000
```

## 📁 Estrutura do Projeto

```
ogp_ineuro/
├── app/
│   ├── static/
│   │   ├── styles.css          # Design system e estilos
│   │   ├── script.js           # JavaScript da interface
│   │   └── design_system.md    # Documentação do design
│   ├── templates/
│   │   ├── chat.html          # Interface principal
│   │   └── design_system.html # Documentação visual
│   ├── main.py               # Servidor principal
│   ├── llm_router.py         # Gerenciamento de LLMs
│   ├── agent.py             # Lógica do assistente
│   ├── memory_agent.py      # Sistema de memória
│   ├── database.py          # Persistência de dados
│   ├── whatsapp.py         # Integração WhatsApp
│   └── command_handler.py   # Processamento de comandos
├── requirements.txt
└── README.md
```

## 🛠️ Tecnologias

- **Backend**: Python, FastAPI
- **Frontend**: HTML5, CSS3, JavaScript
- **LLMs**: Claude, GPT-4, Gemini, DeepSeek
- **WebSocket**: Comunicação em tempo real
- **Design**: Sistema de design próprio

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🔗 Links Úteis

- [Documentação do Design System](app/static/design_system.md)
- [Guia de Desenvolvimento](app/static/progress.md) 