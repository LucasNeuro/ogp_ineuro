# Agente WhatsApp MCP

Um agente de atendimento para WhatsApp que utiliza a MegaAPI para comunicação, Supabase para armazenamento, Mistral para geração de respostas e MCP para funcionalidades avançadas.

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone [seu-repositorio]
cd agent_whatsapp
```

2. Crie um ambiente virtual e ative-o:
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
- Copie o arquivo `.env.example` para `.env`
- Preencha as variáveis com suas credenciais:
  - MegaAPI
  - Supabase
  - Mistral API
  - MCP

## 🏃‍♂️ Executando

1. Inicie o servidor:
```bash
uvicorn app.main:app --reload
```

2. Acesse a documentação da API:
```
http://localhost:8000/docs
```

## 📋 Estrutura do Projeto

```
agent_whatsapp/
├── app/
│   ├── main.py                  # Entrypoint da API FastAPI
│   ├── whatsapp.py             # Recebe e envia mensagens via MegaAPI
│   ├── mistral_client.py        # Conecta com a API do Mistral
│   ├── supabase_client.py       # Manipula mensagens no Supabase
│   ├── mcp_client.py            # Cliente para se conectar a servidores MCP
│   ├── settings.py             # Carrega variáveis do .env
│   └── utils.py                # Funções auxiliares
├── requirements.txt
├── .env
└── README.md
```

## 🔧 Configuração do Webhook

1. Configure o webhook da MegaAPI para apontar para:
```
http://seu-dominio/webhook
```

2. Certifique-se de que o endpoint `/webhook` está acessível publicamente.

## 🤖 Funcionalidades

- Recebimento de mensagens via MegaAPI
- Armazenamento de histórico no Supabase
- Geração de respostas com Mistral
- Integração com servidores MCP
- Endpoint de teste via Swagger

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 