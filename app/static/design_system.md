# I-Neuro Design System

Este documento descreve o design system oficial da plataforma I-Neuro, estabelecendo padrões de cores, tipografia, componentes e estados visuais que devem ser mantidos em toda a aplicação.

## 🎨 Cores

### Cores Primárias
- **Azul Escuro**: `#0E1525` - Fundo principal
- **Azul Médio**: `#1C2333` - Fundo secundário (sidebar, header, footer)
- **Azul Claro**: `#2B3245` - Elementos de UI interativos (cards, inputs)

### Cores de Accent
- **Roxo Primário**: `#6B57FF` - Ações principais, elementos ativos
- **Roxo Secundário**: `#5046E4` - Estados hover
- **Gradiente Roxo**: `linear-gradient(135deg, #6B57FF 0%, #9B66DF 100%)` - Botões, ícones destacados, tags

### Cores de Status
- **Verde (Sucesso)**: `#2EA043` - Indicadores de sucesso, status online
- **Vermelho (Erro)**: `#FF4D4D` - Mensagens de erro, status offline
- **Roxo (Info)**: `#6B57FF` - Informações, badges

## 🔤 Tipografia

### Família de Fontes
- **Principal**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`
- **Monospace**: `'JetBrains Mono', monospace` - Código, prompts

### Tamanhos
- **Grande (Títulos)**: `1.25rem` (20px)
- **Médio (Subtítulos)**: `0.9375rem` (15px)
- **Normal (Corpo)**: `0.875rem` (14px)
- **Pequeno (Badges)**: `0.75rem` (12px)

### Pesos
- **Bold**: `700` - Títulos, ações importantes
- **Medium**: `500` - Subtítulos, destaques
- **Regular**: `400` - Texto normal

## 📐 Espaçamento

### Unidades Base
- **Base**: `0.25rem` (4px)
- **Padrão**: `1rem` (16px)

### Margens e Padding
- **Pequeno**: `0.5rem` (8px)
- **Médio**: `0.75rem 1rem` (12px 16px)
- **Grande**: `1rem 1.5rem` (16px 24px)

## 🎯 Componentes

### Cards Interativos
```css
.interactive-card {
    background: var(--bg-secondary);
    border: 1px solid rgba(107, 87, 255, 0.3);
    border-radius: 8px;
    padding: 1.5rem;
    width: 100%;
}

.interactive-card-header {
    background: linear-gradient(135deg, #6B57FF 0%, #9B66DF 100%);
    border-radius: 8px 8px 0 0;
    padding: 0.75rem 1rem;
}
```

### Tags e Badges
```css
.keyword-tag, .selected-server {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0.75rem;
    background: linear-gradient(135deg, #6B57FF 0%, #9B66DF 100%);
    border-radius: 16px;
    color: white;
    font-size: 0.875rem;
}

.message-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    background: rgba(43, 50, 69, 0.5);
}
```

### Inputs e Selects
```css
.input-field {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 0.75rem 1rem;
    color: var(--text-primary);
    font-size: 0.875rem;
}

select[multiple].input-field {
    padding: 0.5rem;
    min-height: 100px;
}

select[multiple].input-field option:checked {
    background: linear-gradient(135deg, #6B57FF 0%, #9B66DF 100%);
    color: white;
}
```

### Botões
```css
.btn-primary {
    background: linear-gradient(135deg, #6B57FF 0%, #9B66DF 100%);
    color: white;
    border: none;
    padding: 0.75rem 1rem;
    border-radius: 8px;
}

.btn-secondary {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    padding: 0.75rem 1rem;
    border-radius: 8px;
}
```

## 🎭 Estados e Interações

### Hover
- **Botões**: `filter: brightness(1.1)`
- **Cards**: `background: rgba(107, 87, 255, 0.1)`
- **Links**: `border-bottom: 1px solid currentColor`

### Focus
- **Inputs**: `box-shadow: 0 0 0 2px rgba(107, 87, 255, 0.1)`
- **Botões**: `transform: translateY(-1px)`

### Disabled
- **Opacidade**: `0.5`
- **Cursor**: `not-allowed`

## 🌟 Animações

### Transições
```css
.transition-default {
    transition: all 0.2s ease;
}

@keyframes slideIn {
    from {
        transform: translateY(10px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}
```

## 📱 Responsividade

### Breakpoints
- **Mobile**: `max-width: 480px`
- **Tablet**: `max-width: 768px`
- **Desktop**: `min-width: 769px`

### Adaptações
- **Sidebar**: Colapsa em mobile
- **Cards**: Largura total em mobile
- **Grids**: Ajuste de colunas por breakpoint

## 🎯 Boas Práticas

### CSS
- Use variáveis CSS para valores reutilizáveis
- Mantenha especificidade baixa
- Organize por componentes
- Use BEM para nomenclatura

### JavaScript
- Evite manipulação direta do DOM
- Use delegação de eventos
- Mantenha funções pequenas e focadas
- Documente funções complexas

### Acessibilidade
- Use cores com contraste adequado
- Forneça alternativas textuais
- Mantenha foco visível
- Teste com leitores de tela

## Bordas e Sombras

### Bordas
- **Raio**: `8px` - Padrão para todos os componentes
- **Cor**: `var(--border-color)` - `#2B3245`
- **Espessura**: `1px` - Padrão
- **Espessura Destacada**: `2px` - Para elementos destacados ou selecionados

### Sombras
- **Pequena**: `0 2px 4px rgba(0, 0, 0, 0.2)` - Elementos elevados (botões, cards)
- **Média**: `0 4px 8px rgba(0, 0, 0, 0.3)` - Elementos destacados (modais, dropdowns)

## Mensagens

#### Mensagem do Usuário
- **Fundo**: Gradiente roxo
- **Alinhamento**: Direita
- **Cor do Texto**: Branco
- **Raio**: `8px`
- **Máximo**: 85% da largura

#### Mensagem do Assistente
- **Fundo**: Azul claro
- **Alinhamento**: Esquerda
- **Cor do Texto**: Branco
- **Raio**: `8px`
- **Máximo**: 85% da largura

#### Badges das Mensagens
- **Fundo**: Semi-transparente
- **Cor do Texto**: Cinza claro
- **Tamanho**: Pequeno
- **Ícone**: Correspondente ao modelo ou status

## Indicadores

#### Indicador de Carregamento
- **Estilo**: Ícone de cérebro com texto
- **Animação**: Pulsar
- **Cor**: Gradiente roxo
- **Fundo**: Azul médio
- **Raio**: `8px`

#### Indicador de Status
- **Online**: Círculo verde + texto
- **Offline**: Círculo vermelho + texto

## Navegação

#### Mini-Drawer
- **Largura**: `64px` (desktop), `48px` (tablet), `40px` (mobile)
- **Fundo**: Azul médio (`#1C2333`)
- **Posição**: Fixa à esquerda
- **Borda**: `1px` direita `#2B3245`
- **Ícones**: Gradiente roxo
- **Z-index**: `30`

#### Main Drawer
- **Largura**: `240px`
- **Fundo**: Azul médio (`#1C2333`)
- **Posição**: Fixa, após mini-drawer
- **Transição**: Transform `0.3s ease`
- **Estado Colapsado**: Translate -240px no eixo X
- **Borda**: `1px` direita `#2B3245`
- **Z-index**: `20`

#### Layout do Chat
- **Margem Esquerda**: 
  - Drawer Aberto: `304px` (desktop), `288px` (tablet), `280px` (mobile)
  - Drawer Fechado: `64px` (desktop), `48px` (tablet), `40px` (mobile)
- **Transição**: Margin-left `0.3s ease`
- **Fundo**: Azul escuro (`#0E1525`)
- **Borda Esquerda**: `1px` roxo semi-transparente (`rgba(107, 87, 255, 0.3)`)

## Layouts

#### Desktop
- **Mini-Drawer**: Fixo `64px`
- **Main Drawer**: Expansível `240px`
- **Chat**: Alinhado ao drawer, transição suave
- **Largura Total**: `304px` quando expandido

#### Tablet (max-width: 768px)
- **Mini-Drawer**: Fixo `48px`
- **Main Drawer**: Expansível `240px`
- **Chat**: Alinhado ao drawer
- **Largura Total**: `288px` quando expandido

#### Mobile (max-width: 480px)
- **Mini-Drawer**: Fixo `40px`
- **Main Drawer**: Expansível `240px`
- **Chat**: Alinhado ao drawer
- **Largura Total**: `280px` quando expandido

## Iconografia

### Biblioteca
- **Principal**: Font Awesome 6
- **Estilo**: Solid

### Ícones Principais
- **Logo**: `fa-brain` - Cérebro (gradiente roxo)
- **Enviar**: `fa-paper-plane`
- **Upload**: `fa-upload`
- **Salvar**: `fa-save`
- **Fechar**: `fa-times`
- **Chat**: `fa-comments`
- **Dashboard**: `fa-chart-bar`
- **Configurações**: `fa-cog`
- **Base de Conhecimento**: `fa-database`
- **Personalidade**: `fa-user-circle`
- **Prompts**: `fa-code`
- **Ajuda**: `fa-question-circle`

## Princípios de Design

1. **Consistência**: Todos os componentes seguem o mesmo padrão visual em toda a aplicação
2. **Hierarquia**: Elementos importantes são destacados através de cor, tamanho ou posição
3. **Feedback**: Interações do usuário recebem feedback visual imediato
4. **Acessibilidade**: Contraste adequado e áreas de toque dimensionadas corretamente
5. **Responsividade**: Adapta-se a diferentes tamanhos de tela sem perda de funcionalidade 