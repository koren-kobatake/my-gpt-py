import os
import gradio as gr
import openai
from dotenv import load_dotenv

# .envからAPIキーを読み込む
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# 利用可能なモデル
MODELS = [
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-3.5-turbo"
]

def chatbot_response(message, history, model):
    if len(history) > 6:
        history = history[2:]

    messages = [{"role": h["role"], "content": h["content"]} for h in history]
    messages.append({"role": "user", "content": message})

    response = openai.chat.completions.create(
        model=model,
        messages=messages
    )

    return response.choices[0].message.content

def respond(message, chat_history, model):
    reply = chatbot_response(message, chat_history, model)
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": reply})
    return "", chat_history

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## 💬 Chat with OpenAI (latest models)")

    with gr.Row():
        model_dropdown = gr.Dropdown(
            choices=MODELS,
            label="🧠 Select Model",
            value="gpt-4o"
        )
        markdown_toggle = gr.Checkbox(
            label="Markdown形式で表示する",
            value=True
        )

    # render_markdown を最初はTrueに設定
    chatbot = gr.Chatbot(
        label="Chat",
        value=[],
        type='messages',
        render_markdown=True
    )

    msg = gr.Textbox(label="Message", placeholder="Type your message here...")
    clear = gr.ClearButton(components=[msg, chatbot], value="Clear")

    # Markdown表示設定をリアルタイムで反映
    def toggle_markdown(enabled):
        chatbot.render_markdown = enabled

    markdown_toggle.change(fn=toggle_markdown, inputs=markdown_toggle, outputs=[])

    msg.submit(respond, inputs=[msg, chatbot, model_dropdown], outputs=[msg, chatbot])

demo.launch()
