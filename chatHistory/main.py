import os
import json
from datetime import datetime
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

# .envファイルからAPIキーを読み込む
load_dotenv()
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# チャット履歴保存用ディレクトリ
CHAT_HISTORY_DIR = "chat_histories"
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# 履歴ファイルのパス取得
def get_history_path(user_id):
    return os.path.join(CHAT_HISTORY_DIR, f"{user_id}.json")

# 履歴読み込み
def load_history(user_id):
    path = get_history_path(user_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# 履歴保存
def save_history(user_id, history):
    path = get_history_path(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# Chat用メッセージ形式の構築
def build_messages_from_history(history, latest_user_message):
    messages = []

    # 直近3往復だけ抽出（多すぎるとtoken消費）
    recent_turns = history[-6:] if len(history) >= 6 else history

    for h in recent_turns:
        if h['role'] in ['user', 'assistant']:
            messages.append({"role": h['role'], "content": h['content']})

    # 最新のユーザー入力を追加
    messages.append({"role": "user", "content": latest_user_message})

    return messages

# ChatGPTに問い合わせ
def chatbot_response(message, history, user_id):
    full_history = load_history(user_id)
    messages = build_messages_from_history(full_history, message)

    # OpenAI呼び出し
    response = client.chat.completions.create(
        # model="gpt-4o",  # 使用するモデル
        model="chatgpt-4o-latest",
        messages=messages
    )

    reply = response.choices[0].message.content

    # 履歴を保存（userとassistantそれぞれ1件ずつ）
    full_history.append({"role": "user", "content": message, "timestamp": datetime.now().isoformat()})
    full_history.append({"role": "assistant", "content": reply, "timestamp": datetime.now().isoformat()})
    save_history(user_id, full_history)

    return reply

# Gradio UI構築
with gr.Blocks() as app:
    gr.Markdown("# ChatGPT（セッション継続対応）")

    user_id = gr.Textbox(label="ユーザーID（任意のIDを入力）", placeholder="例: user123")
    chatbot = gr.Chatbot(label="Chat", type="messages")
    msg = gr.Textbox(label="メッセージを入力してください", placeholder="こんにちは！と話しかけてみてください")
    clear = gr.Button("チャット履歴をクリア")

    # Gradioで履歴保持用のState
    state = gr.State([])

    # メッセージ送信処理
    def user_submit(user_message, history, user_id):
        if not user_id.strip():
            history.append({"role": "assistant", "content": "⚠️ ユーザーIDを入力してください"})
            return "", history, history  # ← chatbotにもhistoryを返す

        reply = chatbot_response(user_message, history, user_id)

        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply})
        return "", history, history  # ← chatbotにもhistoryを返す

    # 履歴クリア処理
    def clear_session(user_id):
        path = get_history_path(user_id)
        if os.path.exists(path):
            os.remove(path)
        return [], "", []  # ← chatbotもクリア

    # 🛠 イベントバインド：chatbotも出力対象に！
    msg.submit(fn=user_submit, inputs=[msg, state, user_id], outputs=[msg, state, chatbot])
    clear.click(fn=clear_session, inputs=user_id, outputs=[chatbot, msg, state])

# アプリ起動
app.launch(server_port=8500)
