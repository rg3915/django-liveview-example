# Django LiveView - Exemplo de Chat em Tempo Real

## 📖 Sobre o Projeto

Este projeto demonstra o uso do **Django LiveView**, um framework Python que permite construir aplicações web em tempo real (SPAs) usando apenas Django e WebSockets, sem necessidade de frameworks JavaScript separados.

### O que é Django LiveView?

Django LiveView utiliza a tecnologia **HTML over the Wire**, onde:
- Uma conexão WebSocket persistente é estabelecida entre cliente e servidor
- Ações do usuário disparam mensagens JavaScript via WebSocket
- Django processa, renderiza HTML atualizado usando templates
- O HTML é enviado de volta e atualizado no DOM sem recarregar a página

### Features do Projeto

Este projeto implementa **dois exemplos práticos**:

1. **Say Hello (Individual)**: Demonstra atualização em tempo real que afeta apenas o navegador atual
2. **Chat em Tempo Real (Broadcast)**: Chat sincronizado entre todos os navegadores conectados, demonstrando comunicação multi-usuário via WebSocket

### Vantagens do Django LiveView

- ✅ Desenvolvimento 100% em Python (sem JavaScript complexo)
- ✅ Integração nativa com ORM, Forms, Auth e Admin do Django
- ✅ Assíncrono por padrão (Django Channels)
- ✅ Suporte a broadcast para múltiplos usuários
- ✅ ~43% mais rápido que HTMX e ~80% mais rápido que SSR tradicional

---

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.10+
- Docker e Docker Compose (para Redis)
- pip e virtualenv

### Passo 1: Clone e Configure o Ambiente

```bash
# Clone o projeto
git clone <seu-repositorio>
cd django_liveview

# Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
```

### Passo 2: Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DEBUG=True
SECRET_KEY=sua-chave-secreta-aqui
ALLOWED_HOSTS=127.0.0.1,.localhost,0.0.0.0
```

### Passo 3: Inicie o Redis

```bash
docker-compose up -d
```

### Passo 4: Execute as Migrações

```bash
python manage.py migrate
```

### Passo 5: Rode o Servidor

```bash
python manage.py runserver
```

Acesse: **http://127.0.0.1:8000/**

---

## 📂 Estrutura do Projeto e Arquivos Criados

### 1. `docker-compose.yml` (Raiz do projeto)

```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    container_name: django_liveview_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped
volumes:
  redis_data:
```

Configura um container Redis que funciona como message broker para o Django Channels, permitindo comunicação WebSocket entre múltiplos processos/servidores.

---

### 2. `apps/settings.py` (Configurações principais)

**Instalações necessárias:**

```python
INSTALLED_APPS = [
    'daphne',      # Servidor ASGI - DEVE ser o primeiro
    'channels',    # Framework WebSocket
    'liveview',    # Django LiveView
    'django.contrib.admin',
    # ... outros apps
    'apps.core',
]
```

**ASGI Application:**

```python
ASGI_APPLICATION = "apps.asgi.application"
```

**Channel Layers (Redis):**

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

**O que faz:**
- `daphne`: Substitui o servidor WSGI pelo ASGI para suportar WebSockets
- `channels`: Gerencia conexões WebSocket persistentes
- `CHANNEL_LAYERS`: Configura Redis como backend para comunicação entre processos

---

### 3. `apps/asgi.py` (Configuração ASGI)

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from liveview.routing import get_liveview_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(get_liveview_urlpatterns())
            )
        )
    ),
})
```

**O que faz:**
- `ProtocolTypeRouter`: Roteia requisições HTTP e WebSocket separadamente
- `AllowedHostsOriginValidator`: Valida origem das conexões WebSocket por segurança
- `AuthMiddlewareStack`: Disponibiliza autenticação do Django no WebSocket
- `get_liveview_urlpatterns()`: Registra automaticamente as rotas WebSocket do LiveView

---

### 4. `apps/core/urls.py`

```python
from django.urls import path
from apps.core import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
]
```

Define a rota principal que renderiza a página index.

---

### 5. `apps/core/views.py`

```python
from django.shortcuts import render

def index(request):
    template_name = 'index.html'
    return render(request, template_name)
```

View simples que renderiza o template principal. O LiveView funciona via WebSocket, então não precisa de lógica complexa aqui.

---

### 6. `apps/core/templates/base.html`

```html
{% load static %}
{% load liveview %}
<!DOCTYPE html>
<html lang="en" data-room="{% liveview_room_uuid %}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Django Liveview{% endblock %}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css" />
</head>
<body data-controller="page">
  {% block content %}{% endblock content %}

  <script src="{% static 'liveview/liveview.min.js' %}" defer></script>
  {% block js %}{% endblock js %}
</body>
</html>
```

**O que faz:**
- `{% load liveview %}`: Carrega template tags do LiveView
- `data-room="{% liveview_room_uuid %}"`: Gera UUID único para identificar a sala WebSocket
- `data-controller="page"`: Controller Stimulus que gerencia eventos
- `liveview.min.js`: JavaScript do LiveView que gerencia WebSocket e DOM updates

---

### 7. `apps/core/templates/index.html`

```html
{% extends "base.html" %}

{% block content %}
<div style="max-width: 800px; margin: 0 auto; padding: 20px;">
  <!-- Exemplo 1: Say Hello -->
  <section>
    <h2>Exemplo 1: Say Hello (individual)</h2>
    <form>
      <input type="text" name="name" placeholder="Enter your name">
      <button data-liveview-function="say_hello"
              data-action="click->page#run"
              type="button">Say Hello</button>
    </form>
    <div id="greeting"><h1>Hello, World!</h1></div>
  </section>

  <!-- Exemplo 2: Chat -->
  <section>
    <h2>Exemplo 2: Chat em Tempo Real (broadcast)</h2>
    <div id="chat-messages" style="height: 300px; overflow-y: auto;">
      <p>Nenhuma mensagem ainda.</p>
    </div>
    <form>
      <input type="text" name="username" placeholder="Seu nome">
      <input type="text" name="message" placeholder="Mensagem...">
      <button data-liveview-function="send_message"
              data-action="click->page#run"
              type="button">Enviar</button>
    </form>
  </section>
</div>
{% endblock %}

{% block js %}
<script>
  // Auto-scroll + limpar campo
  const chatMessages = document.getElementById('chat-messages');

  const observer = new MutationObserver(() => {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });

  observer.observe(chatMessages, { childList: true, subtree: true });

  document.querySelector('button[data-liveview-function="send_message"]')
    .addEventListener('click', () => {
      setTimeout(() => {
        document.querySelector('input[name="message"]').value = '';
      }, 100);
    });
</script>
{% endblock %}
```

**O que faz:**
- `data-liveview-function`: Nome da função Python que será chamada
- `data-action="click->page#run"`: Stimulus.js captura click e dispara LiveView
- `<form>`: Inputs com `name` são automaticamente capturados pelo LiveView
- JavaScript: MutationObserver detecta novas mensagens e faz auto-scroll

---

### 8. `apps/core/liveview_components/__init__.py`

```python
from . import hello, chat
```

Importa os handlers para que o LiveView os descubra automaticamente.

---

### 9. `apps/core/liveview_components/hello.py`

```python
from liveview import liveview_handler, send
from django.template.loader import render_to_string

@liveview_handler("say_hello")
def say_hello(consumer, content):
    """Handler para o exemplo Say Hello"""
    name = content.get("form", {}).get("name", "World")

    html = render_to_string("hello_message.html", {
        "message": f"Hello, {name}!"
    })

    send(consumer, {
        "target": "#greeting",
        "html": html
    })
```

**O que faz:**
- `@liveview_handler("say_hello")`: Registra função como handler WebSocket
- `content.get("form")`: Recebe dados do formulário HTML
- `render_to_string`: Renderiza template Django
- `send(consumer, ...)`: Envia HTML apenas para o cliente atual (sem broadcast)
- `"target": "#greeting"`: Selector CSS onde o HTML será inserido

---

### 10. `apps/core/liveview_components/chat.py`

```python
from liveview import liveview_handler, send
from django.template.loader import render_to_string
from datetime import datetime

@liveview_handler("send_message")
def send_message(consumer, content):
    """Handler para chat com broadcast"""
    message = content.get("form", {}).get("message", "").strip()
    username = content.get("form", {}).get("username", "Anônimo").strip()

    if not message:
        return

    html = render_to_string("chat_message.html", {
        "username": username,
        "message": message,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })

    send(consumer, {
        "target": "#chat-messages",
        "html": html,
        "append": True
    }, broadcast=True)
```

**O que faz:**
- `broadcast=True`: Envia para TODOS os clientes conectados na mesma sala
- `"append": True`: Adiciona HTML ao invés de substituir (para histórico de chat)
- Valida se mensagem não está vazia antes de processar

---

### 11. `apps/core/templates/hello_message.html`

```html
<h1>{{ message }}</h1>
```

Template simples para o exemplo Say Hello.

---

### 12. `apps/core/templates/chat_message.html`

```html
<div style="padding: 8px; margin-bottom: 5px; background: white;
            border-left: 3px solid #0066cc; border-radius: 4px;">
    <strong style="color: #0066cc;">{{ username }}</strong>
    <small style="color: #999;">({{ timestamp }})</small>
    <p style="margin: 5px 0 0 0;">{{ message }}</p>
</div>
```

Template de cada mensagem do chat com estilização inline.

---

## 🧪 Testando o Chat em Tempo Real

1. **Abra dois navegadores diferentes** (ex: Chrome e Firefox)
2. **Acesse** http://127.0.0.1:8000/ em ambos
3. **No Exemplo 1**, digite um nome e clique "Say Hello" - apenas o navegador atual atualiza
4. **No Exemplo 2**, digite seu nome e uma mensagem - a mensagem aparece em **TODOS** os navegadores instantaneamente!

---

## 📚 Referências

- [Django LiveView - Documentação Oficial](https://django-liveview.andros.dev/)
- [Django Channels](https://channels.readthedocs.io/)
- [Repositório GitHub](https://github.com/Django-LiveView/liveview)

---

## 🤝 Contribuindo

Sinta-se à vontade para abrir issues ou pull requests com melhorias!

---

## 📝 Licença

Este projeto é apenas para fins educacionais e demonstração do Django LiveView.
