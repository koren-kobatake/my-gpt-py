import os
import gradio as gr
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.environ['CLAUDE_API_KEY'])

def chatbot_response(message, history):
    messages = []
    if len(history) > 6:
        history = history[2:]
    for h in history:
        messages.append({"role": "user", "content": h[0]})
        messages.append({"role": "assistant", "content": h[1]})
    messages.append({"role": "user", "content": message})
    
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        # model="claude-3-sonnet-20240229",
        # model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=messages
    )
    return response.content[0].text

app = gr.ChatInterface(chatbot_response, chatbot=gr.Chatbot(type="messages"))
app.launch()
