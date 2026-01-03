from liveview import liveview_handler, send
from django.template.loader import render_to_string


@liveview_handler("say_hello")
def say_hello(consumer, content):
    """Handle 'say_hello' function from client"""
    name = content.get("form", {}).get("name", "World")

    html = render_to_string("hello_message.html", {
        "message": f"Hello, {name}!"
    })

    send(consumer, {
        "target": "#greeting",
        "html": html
    })
