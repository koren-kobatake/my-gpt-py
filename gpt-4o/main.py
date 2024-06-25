import openai
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import time
from openai import OpenAI

# .envファイルからAPIキーを読み込む
load_dotenv()
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# ディレクトリの設定
conversation_dir = './conversation'
archive_dir = './conversation/archive'
memory_file = os.path.join(conversation_dir, 'conversation_history.json')

# ディレクトリが存在しない場合は作成
os.makedirs(conversation_dir, exist_ok=True)
os.makedirs(archive_dir, exist_ok=True)

# 記憶ファイルを読み込む
if os.path.exists(memory_file):
    with open(memory_file, 'r', encoding='utf-8') as f:
        conversation_history = json.load(f)
else:
    conversation_history = []

# ChatGPTに質問する関数
def ask_chatgpt(prompt):
    global conversation_history
    conversation_history.append({"role": "user", "content": prompt})
    
    max_retries = 10  # リトライ回数を増やす
    retry_delay = 30  # リトライ前の待機時間（秒）を増やす
    
    for attempt in range(max_retries):
        try:
            # response = openai.ChatCompletion.create(
            #     model="gpt-3.5-turbo",
            #     messages=conversation_history
            # )

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=conversation_history
            )

            answer = response.choices[0].message.content
            conversation_history.append({"role": "assistant", "content": answer})
            return answer
        # except openai.error.RateLimitError as e:
        #     print(f"Rate limit exceeded. Retrying in {retry_delay} seconds... ({attempt + 1}/{max_retries})")
        #     time.sleep(retry_delay)
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    return "Failed to get a response from ChatGPT after several attempts."

def generate_prompt(history):
    prompt = ""
    for message in history:
        if message["role"] == "user":
            prompt += "User: " + message["content"] + "\n"
        else:
            prompt += "Assistant: " + message["content"] + "\n"
    prompt += "Assistant:"
    return prompt

# 対話のループ
while True:
    user_input = input("You: ")
    
    if user_input.lower() == 'exit':
        break
    elif user_input.lower().startswith('save '):
        # 別名で記憶ファイルを保存
        _, filename = user_input.split(maxsplit=1)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        full_filename = f"{timestamp}_{filename}"
        archive_path = os.path.join(archive_dir, full_filename)
        
        with open(archive_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=4)
        print(f"Conversation history saved as {archive_path}")
        
        # conversation_history.jsonを初期化
        conversation_history = []
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=4)
        print("Conversation history has been reset.")
    else:
        response = ask_chatgpt(user_input)
        print("")
        print("------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
        print(f"ChatGPT: {response}")
        print("------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
        print("")

# 記憶ファイルに保存
with open(memory_file, 'w', encoding='utf-8') as f:
    json.dump(conversation_history, f, ensure_ascii=False, indent=4)
