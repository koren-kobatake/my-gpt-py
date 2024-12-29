import os
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

MODELS = [
    "gpt-4o-2024-11-20",
    "gpt-4o-2024-08-06",
    "gpt-4o-2024-05-13",
    "chatgpt-4o-latest",
    "gpt-3.5-turbo",
    "gpt-4o-mini"
]

def chatbot_response(message, history, model):
    messages = []
    if len(history) > 6:
        history = history[2:]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return completion.choices[0].message.content

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
