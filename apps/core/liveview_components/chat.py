from liveview import liveview_handler, send
from django.template.loader import render_to_string
from datetime import datetime


@liveview_handler("send_message")
def send_message(consumer, content):
    """Handle chat message from client and broadcast to all users"""
    message = content.get("form", {}).get("message", "").strip()
    username = content.get("form", {}).get("username", "Anônimo").strip()

    if not message:
        return

    # Render the message HTML
    html = render_to_string("chat_message.html", {
        "username": username,
        "message": message,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })

    # Broadcast to all connected users in the room
    send(consumer, {
        "target": "#chat-messages",
        "html": html,
        "append": True
    }, broadcast=True)
