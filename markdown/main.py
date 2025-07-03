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

# 最新モデル一覧と特徴（2025年7月時点）
MODEL_INFO = {
    "chatgpt-4o-latest": "chatgpt-4o-latest: GPT-4oの最新バージョンに自動更新される動的モデル。OpenAIの最新研究成果を反映。APIでの研究・評価や、常に最新の性能を体験したい用途に最適。実運用には日付指定モデル推奨。",
    # "gpt-4.5": "GPT-4.5: 感情理解・創造性・自然な対話に優れ、ハルシネーションが大幅減少。高品質な文章生成や創造的タスクに最適。",
    "gpt-4.1": "GPT-4.1: 長文脈処理・高速レスポンス・コーディング能力向上。長文解析やプログラミング支援に最適。",
    "gpt-4.1-mini": "GPT-4.1 mini: 高速・低コスト。リアルタイム応答やコスト重視の業務自動化に最適。",
    "gpt-4.1-nano": "GPT-4.1 nano: 超軽量モデル。コスト・速度重視の用途向け。",
    "gpt-4o": "GPT-4o: テキスト・画像・音声のマルチモーダル対応。マルチモーダルAIアプリや画像＋テキスト処理に最適。",
    "gpt-4o-mini": "GPT-4o mini: GPT-4oの軽量版。日常的なチャットや軽量アプリ向け。",
    # "o3": "o3: 高度な推論能力。数学・科学・複雑な意思決定に強い。",
    # "o3-pro": "o3-pro: o3の高信頼性版。重要な意思決定や複雑な推論に。",
    "o4-mini": "o4-mini: oシリーズの最新推論特化型。日常業務の自動化やリアルタイム性が求められるタスクに。",
    "o4-mini-high": "o4-mini-high: o4-miniの高精度・高信頼性版。ミッションクリティカルな推論や複雑な業務に。",
    "o1": "o1: 強化学習ベースの推論モデル。コード生成や段階的な推論が必要な技術タスクに。",
}

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
        choices=list(MODEL_INFO.keys()),
        value="chatgpt-4o-latest",
        label="モデル選択"
    )

    # モデルの用途を表示
    model_info_display = gr.Markdown(MODEL_INFO["chatgpt-4o-latest"])

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

    # モデル変更時の説明更新
    def update_model_info(selected_model):
        return MODEL_INFO.get(selected_model, "")

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

    model_selector.change(
        fn=update_model_info,
        inputs=[model_selector],
        outputs=model_info_display
    )

app.launch(server_port=8510)
