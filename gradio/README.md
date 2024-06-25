## インストール
Pythonバージョン確認
```bash
# Pythonバージョン確認
python3 --version

# Pipバージョン確認
pip3 --version
```

Pythonをインストールする場合
```bash
# Pythonインストール
sudo yum install python3 -y

# Pipインストール
sudo yum install python3-pip -y
```

仮想環境の作成からPythonファイルの実行
```bash
# ディレクトリに移動
cd ~/xxx/xxx/xxx/my-gpt-py

# 仮想環境の作成
python3 -m venv chatgpt-env

# 仮想環境の有効化
source chatgpt-env/bin/activate

# 必要なパッケージのインストール
pip install openai
pip install python-dotenv
pip install gradio

# Pythonファイルの実行
python main.py

# 仮想環境の無効化
deactivate
```

## 注意点
 * 対話
     * ユーザーとしてメッセージを入力します。
     * exitと入力すると対話を終了します。
     * save <filename>と入力すると、対話履歴が指定のファイル名で保存され、その後conversation_history.jsonが初期化されます。
 * 補足
     * APIキーを実行時に入力させることで、セキュリティが向上します。。
     * conversationおよびconversation/archiveディレクトリが存在しない場合、自動的に作成されます。
     * 別名保存時に、ファイル名の先頭に自動で年月日時分が付与されます。
     * 対話終了時に、自動的にconversation/conversation_history.jsonに対話履歴が保存されます。
