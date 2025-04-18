from fastapi import FastAPI, HTTPException, Request, Form, WebSocket, WebSocketDisconnect, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
import os
import json
from app.whatsapp import whatsapp_client
from app.database import DatabaseClient
from app.agent import ineuro_agent
from app.command_handler import command_handler
from app.memory_agent import MemoryAgent
from typing import List, Dict
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI(
    title="I-Neuro",
    description="API para agente de atendimento via WhatsApp com integração MCP e múltiplos LLMs",
    version="1.0.0"
)

# Configurar templates
templates = Jinja2Templates(directory="app/templates")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/templates/components", StaticFiles(directory="app/templates/components"), name="components")

# Inicializar clientes
db_client = DatabaseClient()
memory_agent = MemoryAgent(db_client)

# Gerenciador de conexões WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message")
            is_command = data.get("is_command", False)
            sender_id = data.get("sender_id", "web_user")
            
            if not message:
                continue
            
            try:
                # Processa a mensagem do usuário com o MemoryAgent
                await memory_agent.process_message(
                    sender_id=sender_id,
                    message=message,
                    is_user=True
                )
                
                # Processa a mensagem
                if is_command or command_handler.is_command(message):
                    response_data = await command_handler.handle_command(message)
                    response_text = response_data.get("response", "")
                    llm_info = {
                        "llm": "system",
                        "model": "command",
                        "classification": "command",
                        "metadata": {"command": True}
                    }
                else:
                    # Obtém contexto relevante do MemoryAgent
                    context = await memory_agent.get_relevant_context(sender_id, message)
                    
                    # Processa com o agente
                    llm_response = await ineuro_agent.process_message(
                        message,
                        context=context
                    )
                    
                    # Extrai informações da resposta
                    response_text = llm_response.get("response", "")
                    llm_info = {
                        "llm": llm_response.get("llm", ""),
                        "model": llm_response.get("model", ""),
                        "classification": llm_response.get("classification", ""),
                        "metadata": llm_response.get("metadata", {})
                    }
                
                # Processa a resposta com o MemoryAgent
                await memory_agent.process_message(
                    sender_id=sender_id,
                    message=response_text,
                    is_user=False,
                    llm_response=llm_info
                )
                
                # Envia resposta ao cliente
                print("Sending response with LLM info:", llm_info)  # Debug log
                await websocket.send_json({
                    "response": response_text,
                    "llm_info": {
                        "name": llm_info["llm"],
                        "model": llm_info["model"],
                        "model_name": llm_info["model"],
                        "total_tokens": llm_info["metadata"].get("total_tokens", 0),
                        "input_tokens": llm_info["metadata"].get("input_tokens", 0),
                        "response_tokens": llm_info["metadata"].get("response_tokens", 0),
                        "classification": llm_info["classification"],
                        "source": llm_info["metadata"].get("source", "llm_router")
                    }
                })
                
            except Exception as e:
                error_message = f"Erro ao processar mensagem: {str(e)}"
                print(f"Error in message processing: {error_message}")
                await websocket.send_json({"error": error_message})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        error_message = str(e)
        await websocket.send_json({"error": f"Erro ao processar mensagem: {error_message}"})
        manager.disconnect(websocket)

@app.on_event("startup")
async def startup_event():
    """Conecta a todos os servidores MCP configurados"""
    await ineuro_agent.connect_servers()

@app.on_event("shutdown")
async def shutdown_event():
    """Desconecta de todos os servidores MCP"""
    await ineuro_agent.disconnect_servers()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/design-system", response_class=HTMLResponse)
async def design_system(request: Request):
    return templates.TemplateResponse("design_system.html", {"request": request})

@app.post("/api/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        message = data.get("message")
        sender_id = data.get("sender_id", "web_user")
        conversation_id = data.get("conversation_id")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Salvar mensagem do usuário
        user_message = await db_client.save_message(
            source="web",
            sender_id=sender_id,
            original_message=message,
            is_user=True,
            conversation_id=conversation_id
        )
        
        # Processar a mensagem
        if command_handler.is_command(message):
            response_data = await command_handler.handle_command(message)
            response_text = response_data.get("response", "")
        else:
            # Processar com o agente e garantir que temos a resposta
            response = await ineuro_agent.process_message(message)
            if isinstance(response, dict):
                response_text = response.get("response", "")
                response_data = response
            else:
                response_text = response
                response_data = {"response": response_text}
        
        # Salvar resposta do agente com informações do LLM
        llm_response = {
            "llm": response_data.get("llm", "ineuro"),
            "model": response_data.get("model", "default"),
            "response": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "classification": response_data.get("classification", ""),
                "tokens_used": response_data.get("tokens_used", 0),
                "source": "web"
            }
        }
        
        await db_client.update_message_with_llm_response(
            message_id=user_message["id"],
            llm_response=llm_response
        )
        
        # Retornar resposta com informações do LLM
        return {
            "response": response_text,
            "llm_info": {
                "name": llm_response["llm"],
                "model": llm_response["model"]
            }
        }
        
    except Exception as e:
        error_message = str(e)
        print(f"Erro no processamento do chat: {error_message}")
        return {"error": f"Erro ao processar mensagem: {error_message}"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        processed_data = whatsapp_client.process_webhook(data)
        
        if not processed_data:
            return {"status": "ignored", "message": "Tipo de mensagem não suportado"}
        
        phone = processed_data["phone"]
        message = processed_data["message"]
        
        # Adiciona mensagem do usuário à conversa
        await db_client.add_message_to_conversation(
            sender_id=phone,
            message=message,
            is_user=True
        )
        
        # Obtém histórico para contexto
        history = await db_client.get_conversation_history(phone, limit=5)
        context = "\n".join([
            f"{'User' if msg['is_user'] else 'Assistant'}: {msg['message']}"
            for msg in history
        ])
        
        # Processa mensagem usando o agente
        llm_response = await ineuro_agent.process_message(message, context)
        
        response_text = llm_response.get("response", "")
        llm_info = {
            "llm": llm_response.get("llm", ""),
            "model": llm_response.get("model", ""),
            "classification": llm_response.get("classification", ""),
            "metadata": llm_response.get("metadata", {})
        }
        
        # Adiciona resposta à conversa
        await db_client.add_message_to_conversation(
            sender_id=phone,
            message=response_text,
            is_user=False,
            llm_response=llm_info
        )
        
        # Envia resposta via WhatsApp
        await whatsapp_client.send_message(
            phone=phone,
            message=response_text
        )
        
        return {"status": "success", "message": "Mensagem processada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/mcp/status")
async def get_mcp_status():
    """Retorna o status de todos os servidores MCP configurados"""
    try:
        status = await ineuro_agent.get_mcp_status()
        return {"status": "success", "servers": status}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/save-card")
async def save_card(request: Request):
    try:
        data = await request.json()
        card_type = data.get("type")
        card_data = data.get("data")
        
        if card_type == "base":
            # Save base card data
            # TODO: Implement saving to database
            print(f"Saving base card data: {card_data}")
            return JSONResponse(content={"success": True, "message": "Base information saved successfully"})
        
        elif card_type == "persona":
            # Save persona card data
            # TODO: Implement saving to database
            print(f"Saving persona card data: {card_data}")
            return JSONResponse(content={"success": True, "message": "Persona information saved successfully"})
        
        elif card_type == "prompt":
            # Save prompt card data
            # TODO: Implement saving to database
            print(f"Saving prompt card data: {card_data}")
            return JSONResponse(content={"success": True, "message": "Prompt information saved successfully"})
        
        else:
            return JSONResponse(content={"success": False, "message": "Invalid card type"}, status_code=400)
    
    except Exception as e:
        print(f"Error saving card data: {str(e)}")
        return JSONResponse(content={"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.post("/api/command/base")
async def handle_base_command(request: Request):
    """Endpoint para processar o comando de base de conhecimento"""
    try:
        form_data = await request.form()
        files = form_data.getlist("files")
        
        if not files:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Nenhum arquivo enviado"}
            )
            
        # Aqui processaria os arquivos recebidos
        # Por enquanto apenas simulamos o sucesso
        
        result = await command_handler._handle_base_command({
            "files": [file.filename for file in files]
        })
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Base de conhecimento atualizada com sucesso"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/command/persona")
async def handle_persona_command(request: Request):
    """Endpoint para processar o comando de persona"""
    try:
        form_data = await request.form()
        description = form_data.get("description", "")
        persona_type = form_data.get("type", "")
        
        if not description and not persona_type:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Descrição ou tipo de persona é necessário"}
            )
            
        result = await command_handler._handle_persona_command({
            "description": description,
            "type": persona_type
        })
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Personalidade configurada com sucesso"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/command/prompt")
async def handle_prompt_command(request: Request):
    """Endpoint para processar o comando de prompt"""
    try:
        form_data = await request.form()
        prompt = form_data.get("prompt", "")
        
        if not prompt:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Prompt é necessário"}
            )
            
        result = await command_handler._handle_prompt_command({
            "prompt": prompt
        })
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Prompt atualizado com sucesso"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"status": "error", "message": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)