// Model icon mappings
const MODEL_ICONS = {
    'openai': 'fa-robot',
    'anthropic': 'fa-comment-dots',
    'mistral': 'fa-wind',
    'gemini': 'fa-gem',
    'deepseek': 'fa-search',
    'system': 'fa-brain',
    'default': 'fa-microchip'
};

// Interactive card templates
const CARD_TEMPLATES = {
    'base': {
        title: 'Base de Conhecimento',
        icon: 'fa-database',
        fields: [
            {
                type: 'file',
                name: 'knowledge_files',
                label: 'Arquivos de Conhecimento',
                accept: '.txt,.pdf,.doc,.docx',
                multiple: true
            },
            {
                type: 'text',
                name: 'knowledge_name',
                label: 'Nome da Base',
                placeholder: 'Ex: Base de Documentos Técnicos'
            },
            {
                type: 'textarea',
                name: 'knowledge_description',
                label: 'Descrição da Base',
                placeholder: 'Descreva o conteúdo e propósito desta base de conhecimento...'
            }
        ]
    },
    'persona': {
        title: 'Personalidade do Agente',
        icon: 'fa-user-circle',
        fields: [
            {
                type: 'text',
                name: 'persona_name',
                label: 'Nome do Agente',
                placeholder: 'Ex: Assistente Técnico'
            },
            {
                type: 'select',
                name: 'persona_type',
                label: 'Tipo de Personalidade',
                options: [
                    { value: 'technical', label: 'Técnico' },
                    { value: 'friendly', label: 'Amigável' },
                    { value: 'professional', label: 'Profissional' },
                    { value: 'expert', label: 'Especialista' }
                ]
            },
            {
                type: 'textarea',
                name: 'persona_description',
                label: 'Descrição da Personalidade',
                placeholder: 'Descreva como o agente deve se comportar e interagir...'
            },
            {
                type: 'textarea',
                name: 'persona_examples',
                label: 'Exemplos de Interação',
                placeholder: 'Forneça exemplos de como o agente deve responder...'
            }
        ]
    },
    'prompt': {
        title: 'Configuração de Prompt',
        icon: 'fa-code',
        fields: [
            {
                type: 'text',
                name: 'prompt_name',
                label: 'Nome do Prompt',
                placeholder: 'Ex: Prompt de Análise Técnica'
            },
            {
                type: 'select',
                name: 'prompt_type',
                label: 'Tipo de Prompt',
                options: [
                    { value: 'system', label: 'Sistema' },
                    { value: 'user', label: 'Usuário' },
                    { value: 'assistant', label: 'Assistente' }
                ]
            },
            {
                type: 'textarea',
                name: 'prompt_content',
                label: 'Conteúdo do Prompt',
                placeholder: 'Digite o prompt base...'
            },
            {
                type: 'file',
                name: 'prompt_file',
                label: 'Arquivo de Prompt (opcional)',
                accept: '.txt,.md',
                multiple: false
            }
        ]
    }
};

// DOM Elements
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const chatMessages = document.getElementById('chat-messages');
const thinkingIndicator = document.getElementById('thinking-indicator');
const interactiveCard = document.getElementById('interactive-card');

// WebSocket connection
let ws = null;
let isConnected = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000; // 2 segundos

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket conectado');
        isConnected = true;
        reconnectAttempts = 0;
        updateConnectionStatus(true);
        hideThinkingIndicator();
    };
    
    ws.onclose = () => {
        console.log('WebSocket desconectado');
        isConnected = false;
        updateConnectionStatus(false);
        
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            setTimeout(connectWebSocket, RECONNECT_DELAY * reconnectAttempts);
        } else {
            showError('Não foi possível estabelecer conexão com o servidor. Por favor, recarregue a página.');
        }
    };
    
    ws.onerror = (error) => {
        console.error('Erro no WebSocket:', error);
        showError('Erro de conexão com o servidor');
    };
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log("Recebido do servidor:", data);
            handleMessage(data);
        } catch (error) {
            console.error('Erro ao processar mensagem:', error);
            showError('Erro ao processar resposta do servidor');
        }
    };
}

function updateConnectionStatus(connected) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-indicator span');
    
    if (statusDot && statusText) {
        if (connected) {
            statusDot.style.backgroundColor = 'var(--success-color)';
            statusText.textContent = 'Assistente Virtual Ativo';
        } else {
            statusDot.style.backgroundColor = 'var(--error-color)';
            statusText.textContent = 'Desconectado';
        }
    }
}

function showError(message) {
    const errorMessage = createMessage(message, false, {
        model: 'system',
        error: true
    });
    errorMessage.classList.add('error-message');
    chatMessages.appendChild(errorMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function createMessage(content, isUser = false, metadata = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : ''}`;
    
    // Message badge with model info
    if (!isUser && metadata) {
        const badgeDiv = document.createElement('div');
        badgeDiv.className = 'message-badge';
        
        // Set data-model attribute for CSS styling
        if (metadata.model) {
            badgeDiv.setAttribute('data-model', metadata.model.toLowerCase());
        }
        
        // Model icon
        const modelType = metadata.llm || 'default';
        const iconClass = MODEL_ICONS[modelType] || MODEL_ICONS.default;
        
        // Format model name and tokens
        const modelName = metadata.model || 'default';
        const totalTokens = metadata.metadata?.total_tokens || '';
        
        badgeDiv.innerHTML = `
            <i class="fas ${iconClass}"></i>
            <span>I-Neuro (${modelName}) ${totalTokens ? '• ' + totalTokens + ' tokens' : ''}</span>
        `;
        
        messageDiv.appendChild(badgeDiv);
    }
    
    // Message content with formatting
    const textDiv = document.createElement('div');
    textDiv.className = 'message-content';
    
    // Convert markdown to HTML and preserve emojis
    const formattedContent = marked.parse(content);
    textDiv.innerHTML = formattedContent;
    
    // Add message content
    messageDiv.appendChild(textDiv);
    
    return messageDiv;
}

// Função para formatar mensagem mantendo emojis e markdown
function formatMessage(content) {
    return marked.parse(content);
}

// Configuração do Marked para preservar emojis
marked.setOptions({
    gfm: true,
    breaks: true,
    mangle: false,
    headerIds: false,
    emoji: true
});

function createInteractiveCard(type) {
    const template = CARD_TEMPLATES[type];
    if (!template) return null;

    const card = document.createElement('div');
    card.className = 'interactive-card';
    card.innerHTML = `
        <div class="interactive-card-header">
            <i class="fas ${template.icon}"></i>
            <h3>${template.title}</h3>
        </div>
        <div class="interactive-card-content">
            <form id="${type}-form">
                ${template.fields.map(field => {
                    switch (field.type) {
                        case 'file':
                            return `
                                <div class="form-group">
                                    <label for="${field.name}">${field.label}</label>
                                    <div class="file-upload-area" id="${field.name}_area">
                                        <i class="fas fa-cloud-upload-alt"></i>
                                        <p>Arraste arquivos ou clique para selecionar</p>
                                        <input type="file" id="${field.name}" name="${field.name}"
                                            accept="${field.accept}" ${field.multiple ? 'multiple' : ''} class="hidden">
                                    </div>
                                    <div id="${field.name}_list" class="file-list hidden"></div>
                                </div>
                            `;
                        case 'text':
                            return `
                                <div class="form-group">
                                    <label for="${field.name}">${field.label}</label>
                                    <input type="text" id="${field.name}" name="${field.name}"
                                        placeholder="${field.placeholder}" class="input-field">
                                </div>
                            `;
                        case 'textarea':
                            return `
                                <div class="form-group">
                                    <label for="${field.name}">${field.label}</label>
                                    <textarea id="${field.name}" name="${field.name}"
                                        placeholder="${field.placeholder}" class="input-field"
                                        rows="4"></textarea>
                                </div>
                            `;
                        case 'select':
                            return `
                                <div class="form-group">
                                    <label for="${field.name}">${field.label}</label>
                                    <select id="${field.name}" name="${field.name}" class="input-field">
                                        ${field.options.map(opt => 
                                            `<option value="${opt.value}">${opt.label}</option>`
                                        ).join('')}
                                    </select>
                                </div>
                            `;
                        default:
                            return '';
                    }
                }).join('')}
            </form>
        </div>
        <div class="interactive-card-footer">
            <button class="btn btn-secondary" onclick="this.closest('.interactive-card').remove()">
                <i class="fas fa-times"></i> Cancelar
            </button>
            <button class="btn btn-primary" onclick="handleCardSave('${type}', this.closest('.interactive-card'))">
                <i class="fas fa-save"></i> Salvar
            </button>
        </div>
    `;

    // Adicionar listeners para upload de arquivo
    const fileInputs = card.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        const area = document.getElementById(`${input.id}_area`);
        const list = document.getElementById(`${input.id}_list`);

        area.addEventListener('click', () => input.click());
        area.addEventListener('dragover', e => {
            e.preventDefault();
            area.classList.add('dragover');
        });
        area.addEventListener('dragleave', () => area.classList.remove('dragover'));
        area.addEventListener('drop', e => {
            e.preventDefault();
            area.classList.remove('dragover');
            input.files = e.dataTransfer.files;
            updateFileList(input);
        });

        input.addEventListener('change', () => updateFileList(input));
    });

    return card;
}

function updateFileList(input) {
    const list = document.getElementById(`${input.id}_list`);
    if (!list) return;

    list.innerHTML = '';
    list.classList.remove('hidden');

    Array.from(input.files).forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <i class="fas fa-file"></i>
            <span>${file.name}</span>
            <span class="file-size">${(file.size / 1024).toFixed(1)} KB</span>
        `;
        list.appendChild(item);
    });
}

function showThinkingIndicator() {
    thinkingIndicator.classList.add('visible');
}

function hideThinkingIndicator() {
    thinkingIndicator.classList.remove('visible');
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || !isConnected) return;
    
    messageInput.value = '';
    chatMessages.appendChild(createMessage(message, true));
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    showThinkingIndicator();
    
    try {
        ws.send(JSON.stringify({ message }));
    } catch (error) {
        console.error('Erro ao enviar mensagem:', error);
        showError('Erro ao enviar mensagem');
        hideThinkingIndicator();
    }
}

function handleMessage(data) {
    hideThinkingIndicator();
    
    if (data.type === 'interactive_card') {
        console.log('Recebido card interativo:', data);
        const messageDiv = createMessage('', false, { model: 'system' });
        const card = createInteractiveCard(data.command);
        messageDiv.appendChild(card);
        chatMessages.appendChild(messageDiv);
    } else {
        if (data.error) {
            showError(data.error);
        } else if (data.response) {
            chatMessages.appendChild(createMessage(data.response, false, {
                model: data.model || 'default',
                score: data.score || 1.0
            }));
        }
    }
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Adicionar ouvinte para uploads de arquivo
document.addEventListener('change', function(e) {
    if (e.target.type === 'file') {
        const fileListId = e.target.id.replace('_file', '_list').replace('_files', '_list');
        const fileList = document.getElementById(fileListId) || document.getElementById('selected_files');
        
        if (fileList) {
            fileList.innerHTML = '';
            fileList.classList.remove('hidden');
            
            Array.from(e.target.files).forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.innerHTML = `
                    <i class="fas fa-file"></i>
                    <span>${file.name}</span>
                    <span class="text-sm text-secondary ml-auto">${(file.size / 1024).toFixed(1)} KB</span>
                `;
                fileList.appendChild(fileItem);
            });
        }
        
        // Preview para arquivos markdown
        if (e.target.id === 'prompt_file' && e.target.files[0]) {
            const preview = document.getElementById('prompt_preview');
            if (preview) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    preview.textContent = event.target.result;
                };
                reader.readAsText(e.target.files[0]);
            }
        }
    }
});

// Processador de cliques nos botões dos cards
document.addEventListener('click', async function(e) {
    const button = e.target.closest('button[data-action]');
    if (!button) return;
    
    const action = button.dataset.action;
    const command = button.dataset.command;
    
    console.log(`Ação acionada: ${action} para comando: ${command}`);
    
    showThinkingIndicator();
    
    try {
        const formData = new FormData();
        
        // Coleta dados específicos para cada tipo de comando
        switch (command) {
            case 'base':
                const baseFiles = document.getElementById('base_files');
                if (baseFiles && baseFiles.files.length > 0) {
                    Array.from(baseFiles.files).forEach(file => {
                        formData.append('files', file);
                    });
                } else {
                    throw new Error('Nenhum arquivo selecionado');
                }
                break;
                
            case 'persona':
                const description = document.getElementById('persona_description');
                const type = document.getElementById('persona_type');
                
                if (description && description.value) {
                    formData.append('description', description.value);
                }
                
                if (type && type.value) {
                    formData.append('type', type.value);
                }
                
                if (!description.value && !type.value) {
                    throw new Error('Preencha a descrição ou selecione um tipo');
                }
                break;
                
            case 'prompt':
                const promptFile = document.getElementById('prompt_file');
                if (promptFile && promptFile.files.length > 0) {
                    formData.append('file', promptFile.files[0]);
                } else {
                    throw new Error('Nenhum arquivo de prompt selecionado');
                }
                break;
                
            default:
                throw new Error('Tipo de comando desconhecido');
        }
        
        // Envia a requisição para o servidor
        const response = await fetch(`/api/command/${command}`, {
            method: 'POST',
            body: formData
        });
        
        // Processa a resposta
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Exibe mensagem de sucesso
        chatMessages.appendChild(createMessage(data.response || 'Comando executado com sucesso', false, {
            model: 'system'
        }));
        
        // Esconde o card interativo
        interactiveCard.classList.add('hidden');
        
    } catch (error) {
        console.error('Erro na ação:', error);
        showError(error.message || 'Erro ao processar ação');
    } finally {
        hideThinkingIndicator();
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});

// Função para lidar com o salvamento dos cards
async function handleCardSave(command, card) {
    showThinkingIndicator();
    
    try {
        const formData = new FormData();
        
        switch (command) {
            case '/base':
                const fileInput = card.querySelector('input[type="file"]');
                if (fileInput && fileInput.files.length > 0) {
                    Array.from(fileInput.files).forEach(file => {
                        formData.append('files', file);
                    });
                } else {
                    throw new Error('Nenhum arquivo selecionado');
                }
                break;
                
            case '/persona':
                const description = card.querySelector('#persona_description');
                const type = card.querySelector('#persona_type');
                
                if (description && description.value) {
                    formData.append('description', description.value);
                }
                if (type && type.value) {
                    formData.append('type', type.value);
                }
                if (!description?.value && !type?.value) {
                    throw new Error('Preencha a descrição ou selecione um tipo');
                }
                break;
                
            case '/prompt':
                const promptInput = card.querySelector('#prompt_text');
                if (promptInput && promptInput.value) {
                    formData.append('prompt', promptInput.value);
                } else {
                    throw new Error('Digite um prompt');
                }
                break;
        }
        
        const cmdType = command.replace('/', '');
        const response = await fetch(`/api/command/${cmdType}`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        chatMessages.appendChild(createMessage(result.message || 'Comando executado com sucesso', false, {
            model: 'system'
        }));
        card.remove();
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideThinkingIndicator();
    }
}

// Atualiza o evento de clique nos badges de comando
document.addEventListener('DOMContentLoaded', function() {
    const commandBadges = document.querySelectorAll('.command-badge');
    
    commandBadges.forEach(badge => {
        badge.addEventListener('click', () => {
            const command = badge.dataset.command.replace('/', '');
            const card = createInteractiveCard(command);
            
            if (card) {
                const messagesContainer = document.getElementById('chat-messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message assistant';
                messageDiv.appendChild(card);
                messagesContainer.appendChild(messageDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        });
    });
});

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();
    
    // Atualiza ícones para cérebro roxo
    document.querySelectorAll('.logo-icon').forEach(icon => {
        icon.innerHTML = '<i class="fas fa-brain"></i>';
    });
    
    sendButton.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Mensagem inicial
    chatMessages.appendChild(createMessage('Olá! Sou o assistente virtual I-Neuro. Como posso ajudar você hoje?', false, {
        model: 'system'
    }));
}); 