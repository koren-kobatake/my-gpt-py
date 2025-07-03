import os
import json
from datetime import datetime
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

# .envからAPIキーを読み込む
load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ディレクトリ作成
CHAT_HISTORY_DIR = "chat_histories"
MARKDOWN_EXPORT_DIR = "markdown_exports"
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
os.makedirs(MARKDOWN_EXPORT_DIR, exist_ok=True)

# チャット履歴ファイルパス
def get_history_path(user_id):
    return os.path.join(CHAT_HISTORY_DIR, f"{user_id}.json")

# チャット履歴読み込み
def load_history(user_id):
    path = get_history_path(user_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# チャット履歴保存
def save_history(user_id, history):
    path = get_history_path(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# ChatGPT向けのメッセージ形式へ変換
def build_messages_from_history(history, latest_user_message):
    messages = [{"role": h["role"], "content": h["content"]}
                for h in history if h["role"] in ["user", "assistant"]]
    messages.append({"role": "user", "content": latest_user_message})
    return messages[-10:]

# ChatGPT に問い合わせ（モデルを引数化）
def chatbot_response(message, full_history, user_id, model_name):
    messages = build_messages_from_history(full_history, message)

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"⚠️ APIエラー: {e}"

    # 履歴に保存
    full_history.append({"role": "user", "content": message, "timestamp": datetime.now().isoformat()})
    full_history.append({"role": "assistant", "content": reply, "timestamp": datetime.now().isoformat()})
    save_history(user_id, full_history)

    return reply, full_history

# 最新の質問と回答のみMarkdown出力
def export_latest_to_markdown(user_id, history):
    if not history or len(history) < 2:
        return "⚠️ 出力する履歴がありません"

    latest_assistant_idx = len(history) - 1
    latest_user_idx = latest_assistant_idx - 1

    if history[latest_assistant_idx]["role"] != "assistant":
        return "⚠️ 最新がアシスタントの応答ではありません"

    question = history[latest_user_idx]["content"] if history[latest_user_idx]["role"] == "user" else "（質問なし）"
    answer = history[latest_assistant_idx]["content"]
    timestamp = history[latest_assistant_idx].get("timestamp", datetime.now().isoformat())
    safe_time = timestamp.replace(":", "-").replace(".", "-")
    filename = f"{user_id}_{safe_time}.md"
    path = os.path.join(MARKDOWN_EXPORT_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# 質問\n\n{question}\n\n# 回答\n\n{answer}")

    return f"✅ Markdown出力完了: {filename}"

# Gradio アプリ
with gr.Blocks() as app:
    gr.Markdown("# ChatGPT（最新の質問＆回答のみMarkdown保存）")

    user_id = gr.Textbox(label="ユーザーID", placeholder="例: user_xyz")

    model_selector = gr.Dropdown(
        choices=["chatgpt-4o-latest", "gpt-4o"],
        value="gpt-4o",
        label="モデル選択"
    )

    chatbot = gr.Chatbot(label="チャット", type="messages")
    msg = gr.Textbox(label="メッセージを入力")
    clear = gr.Button("チャット履歴をクリア")
    state = gr.State([])  # チャット履歴
    output_status = gr.Textbox(label="出力ステータス", interactive=False)
    export_button = gr.Button("📝 最新の回答をMarkdown保存")

    # Gradio用チャット形式に変換
    def update_chatbot_display(history):
        return [{"role": h["role"], "content": h["content"]}
                for h in history if h["role"] in ["user", "assistant"]]

    # メッセージ送信処理
    def user_submit(user_message, history, user_id, model_name):
        if not user_id.strip():
            history.append({"role": "assistant", "content": "⚠️ ユーザーIDを入力してください"})
            return "", history, update_chatbot_display(history)

        history = history if history else load_history(user_id)
        reply, new_history = chatbot_response(user_message, history, user_id, model_name)
        return "", new_history, update_chatbot_display(new_history)

    # チャット履歴クリア
    def clear_session(user_id):
        path = get_history_path(user_id)
        if os.path.exists(path):
            os.remove(path)
        return [], "", [], ""

    # Markdown出力ボタン処理
    def export_markdown(user_id, history):
        return export_latest_to_markdown(user_id, history)

    # イベント設定
    msg.submit(
        fn=user_submit,
        inputs=[msg, state, user_id, model_selector],
        outputs=[msg, state, chatbot]
    )

    clear.click(
        fn=clear_session,
        inputs=user_id,
        outputs=[state, msg, chatbot, output_status]
    )

    export_button.click(
        fn=export_markdown,
        inputs=[user_id, state],
        outputs=output_status
    )

app.launch(server_port=8510)