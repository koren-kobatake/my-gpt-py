import os
import gradio as gr
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.environ['CLAUDE_API_KEY'])

MODELS = [
    "claude-3-haiku-20240307",
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229"
]

def chatbot_response(message, history, model):
    messages = []
    if len(history) > 6:
        history = history[2:]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})
    
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=messages
    )
    return response.content[0].text

with gr.Blocks() as app:
    model_dropdown = gr.Dropdown(choices=MODELS, label="Select Model", value=MODELS[0])
    chatbot = gr.Chatbot(label="Chat", type="messages")
    msg = gr.Textbox(label="Message", placeholder="Type your message here...")
    clear = gr.ClearButton([msg, chatbot])

    def respond(message, chat_history, model):
        bot_message = chatbot_response(message, chat_history, model)
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": bot_message})
        return "", chat_history

    msg.submit(respond, [msg, chatbot, model_dropdown], [msg, chatbot])

app.launch()
