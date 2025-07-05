import os
import json
from datetime import datetime
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
import fastapi

# .envからAPIキーを読み込む
load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

CHAT_HISTORY_DIR = "chat_histories"
MARKDOWN_EXPORT_DIR = "markdown_exports"
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
os.makedirs(MARKDOWN_EXPORT_DIR, exist_ok=True)

MODEL_INFO = {
    "chatgpt-4o-latest": "chatgpt-4o-latest: GPT-4oの最新バージョンに自動更新される動的モデル。",
    "gpt-4.1": "GPT-4.1: 長文脈処理・高速レスポンス・コーディング能力向上。",
    "gpt-4.1-mini": "GPT-4.1 mini: 高速・低コスト。",
    "gpt-4.1-nano": "GPT-4.1 nano: 超軽量モデル。",
    "gpt-4o": "GPT-4o: テキスト・画像・音声のマルチモーダル対応。",
    "gpt-4o-mini": "GPT-4o mini: GPT-4oの軽量版。",
    "o4-mini": "o4-mini: oシリーズの最新推論特化型。",
    "o4-mini-high": "o4-mini-high: o4-miniの高精度・高信頼性版。",
    "o1": "o1: 強化学習ベースの推論モデル。"
}

def get_history_path(chat_id):
    return os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")

def load_history(chat_id):
    path = get_history_path(chat_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(chat_id, history):
    path = get_history_path(chat_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def build_messages_from_history(history, latest_user_message):
    messages = [{"role": h["role"], "content": h["content"]}
                for h in history if h["role"] in ["user", "assistant"]]
    messages.append({"role": "user", "content": latest_user_message})
    return messages[-10:]

def chatbot_response(message, full_history, chat_id, model_name, save=False):
    messages = build_messages_from_history(full_history, message)
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"⚠️ APIエラー: {e}"

    full_history.append({"role": "user", "content": message, "timestamp": datetime.now().isoformat()})
    full_history.append({"role": "assistant", "content": reply, "timestamp": datetime.now().isoformat()})

    if save and chat_id:
        save_history(chat_id, full_history)

    return reply, full_history

def export_latest_to_markdown(chat_id, history):
    if not history or len(history) < 2:
        return "⚠️ 出力する履歴がありません"

    latest_assistant_idx = len(history) - 1
    latest_chat_idx = latest_assistant_idx - 1

    if history[latest_assistant_idx]["role"] != "assistant":
        return "⚠️ 最新がアシスタントの応答ではありません"

    question = history[latest_chat_idx]["content"] if history[latest_chat_idx]["role"] == "user" else "（質問なし）"
    answer = history[latest_assistant_idx]["content"]
    timestamp = history[latest_assistant_idx].get("timestamp", datetime.now().isoformat())
    safe_time = timestamp.replace(":", "-").replace(".", "-")
    filename = f"{chat_id}_{safe_time}.md"
    path = os.path.join(MARKDOWN_EXPORT_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# 質問\n\n{question}\n\n# 回答\n\n{answer}")

    return f"✅ Markdown出力完了: {filename}"

def get_existing_chat_ids():
    return [f.replace(".json", "") for f in os.listdir(CHAT_HISTORY_DIR) if f.endswith(".json")]

def update_chatbot_display(history):
    return [{"role": h["role"], "content": h["content"]}
            for h in history if h["role"] in ["user", "assistant"]]

def get_chat_id(text_input, dropdown_input, mode):
    return text_input.strip() if mode == "新規入力" else dropdown_input

with gr.Blocks() as app:
    gr.Markdown("## 🧠 ChatGPT Markdown出力対応アプリ")

    with gr.Row():
        # 左ペイン
        with gr.Column(scale=1):
            save_mode = gr.Radio(["履歴を残す", "履歴を残さない"], value="履歴を残す", label="履歴保存モード")

            chat_id_mode = gr.Radio(["新規入力", "既存から選択"], value="新規入力", label="チャットIDの指定方法")

            chat_id_text = gr.Textbox(label="チャットID（新規）", placeholder="例: user_abc", visible=True)
            chat_id_dropdown = gr.Dropdown(choices=get_existing_chat_ids(), label="チャットID（既存）", visible=False)

            model_selector = gr.Dropdown(choices=list(MODEL_INFO.keys()), value="chatgpt-4o-latest", label="モデル選択")
            model_info_display = gr.Markdown(MODEL_INFO["chatgpt-4o-latest"])

        # 右ペイン
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="チャット", type="messages")
            msg = gr.Textbox(label="メッセージを入力")
            with gr.Row():
                clear = gr.Button("🧹 チャット履歴クリア")
                export_button = gr.Button("📝 Markdown保存")
            output_status = gr.Textbox(label="出力ステータス", interactive=False)

    state = gr.State([])

    def toggle_chat_id_inputs(mode):
        return (
            gr.update(visible=(mode == "新規入力")),
            gr.update(visible=(mode == "既存から選択"))
        )

    chat_id_mode.change(fn=toggle_chat_id_inputs, inputs=[chat_id_mode], outputs=[chat_id_text, chat_id_dropdown])

    def on_select_existing_chat_id(selected_id):
        history = load_history(selected_id) if selected_id else []
        return history, update_chatbot_display(history)

    chat_id_dropdown.change(fn=on_select_existing_chat_id, inputs=chat_id_dropdown, outputs=[state, chatbot])

    def user_submit(user_message, history, chat_id_text_val, chat_id_dropdown_val, chat_id_mode_val, model_name, save_option):
        save_enabled = (save_option == "履歴を残す")
        current_id = get_chat_id(chat_id_text_val, chat_id_dropdown_val, chat_id_mode_val)

        if save_enabled and not current_id:
            history.append({"role": "assistant", "content": "⚠️ チャットIDを入力または選択してください"})
            return user_message, history, update_chatbot_display(history)

        if save_enabled and history == []:
            history = load_history(current_id)

        reply, updated_history = chatbot_response(user_message, history, current_id, model_name, save=save_enabled)
        return "", updated_history, update_chatbot_display(updated_history)

    msg.submit(
        fn=user_submit,
        inputs=[msg, state, chat_id_text, chat_id_dropdown, chat_id_mode, model_selector, save_mode],
        outputs=[msg, state, chatbot]
    )

    model_selector.change(fn=lambda selected: MODEL_INFO[selected], inputs=model_selector, outputs=model_info_display)

    def do_clear(chat_id_text_val, chat_id_dropdown_val, chat_id_mode_val):
        chat_id_val = get_chat_id(chat_id_text_val, chat_id_dropdown_val, chat_id_mode_val)
        if chat_id_val:
            path = get_history_path(chat_id_val)
            if os.path.exists(path):
                os.remove(path)
        return [], "", [], "✅ チャット履歴をクリアしました"

    clear.click(fn=do_clear, inputs=[chat_id_text, chat_id_dropdown, chat_id_mode],
                outputs=[state, msg, chatbot, output_status])

    def do_export(chat_id_text_val, chat_id_dropdown_val, chat_id_mode_val, history, save_option):
        if save_option != "履歴を残す":
            return "⚠️ Markdown出力は履歴保存モードのみ対応しています"
        chat_id_val = get_chat_id(chat_id_text_val, chat_id_dropdown_val, chat_id_mode_val)
        if not chat_id_val:
            return "⚠️ チャットIDが未指定です"
        return export_latest_to_markdown(chat_id_val, history)

    export_button.click(fn=do_export,
                        inputs=[chat_id_text, chat_id_dropdown, chat_id_mode, state, save_mode],
                        outputs=output_status)

    # app.launch(debug=True, server_port=8520)
    app_api = fastapi.FastAPI()
    app_api = gr.mount_gradio_app(app_api, app, path="/gradio")