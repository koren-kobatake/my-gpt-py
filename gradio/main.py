import os
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def chatbot_response(message, history):
    messages = []
    if len(history) > 6:
        history = history[2:]
    for h in history:
        messages.append({"role": "user", "content": h[0]})
        messages.append({"role": "assistant", "content": h[1]})
    messages.append({"role": "user", "content": message})
    completion = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=messages,
    )
    return completion.choices[0].message.content

app = gr.ChatInterface(chatbot_response)
app.launch()
