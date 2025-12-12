# <img src="https://github.com/kei-mag/human-chat-completions/blob/main/src/assets/icon.png?raw=true" height="50" style="vertical-align: bottom;"> Human Chat Completions

<div style="display: flex; justify-content: space-around;">
<p style="font-size: 16px;"><b>日本語</b> / <a href="README_en.md">English</a></p> <img src="https://github.com/miyamoto-hai-lab/human-chat-completions/actions/workflows/release.yml/badge.svg">
</div>

Human Chat Completions は、[Flet](https://flet.dev) で構築された オズの魔法使い法 (Wizard of Oz) 実験用のデスクトップチャットアプリケーションです。

OpenAIの `v1/chat/completions` APIと互換性のあるエンドポイントを提供しますが、リクエストは自動処理されず、Flet製のチャット画面（オペレーターUI）に転送されます。

最大の特徴は 「**LLMコパイロット（応答候補生成）**」機能 です。バックグラウンドで本物のLLMがドラフトを作成し、人間のオペレーターはそれを 編集・修正・承認 してからクライアントに送信できます。これにより、ゼロから返信を書く負担を減らしつつ、正確なコントロールが可能になります。

基本はすべてLLMに応答させ、人間による介入が必要になった場合のみ、介入することもできます。
これにより、**「完全な人間による応答」「AIドラフトの修正」「完全自動のAI応答」を状況に応じて自由に切り替えることが可能**です。

## 主な特徴
- **API完全互換**: 既存のチャットアプリの接続先 (base_url) を変えるだけで、AI応答から人間介入型へ切り替え可能。
- **Flet GUI**: Pythonだけで記述されたモダンなオペレーター用ダッシュボード（Webブラウザまたはデスクトップアプリとして動作）。
- **LLMコパイロット (人間とAIの協働)**:
    - ユーザーの問いに対し、まずは内部のLLMが「下書き」を生成。
    オペレーターはその下書きを採用するか、修正して送信するかを選択可能。
- **ストリーミング対応**: `stream: true` に対応。人間がタイピング（または修正）した内容を、リアルタイムでクライアントに配信します。
- **ログ収集**: 「ユーザー入力」「AIのドラフト」「人間が修正した最終回答」の3点を記録し、比較研究に役立てることができます。

## 利用シーン
1. **WoZ法によるプロトタイピング**: 開発初期段階で、理想的なAIの挙動を人間が演じて検証する。
2. **RLHF用データ作成**: AIの回答を人間がリアルタイムで修正し、高品質な学習データを作成する。
3. **リスク管理**: センシティブな話題に対して、オペレーターが介入して安全な回答に書き換えるテストを行う。

## 使い方
### インストールと起動
[最新のRelease](https://github.com/miyamoto-hai-lab/human-chat-completions/releases/latest)から

### クライアント側のコード例
```python
from openai import OpenAI

client = OpenAI(
    api_key="dummy",                     # APIキーはダミーでOK
    base_url="http://localhost:8000/v1/chat/completions"  # サーバーのアドレスを指定
)

# リクエストを送信すると、Fletの画面に着信します
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Pythonのジョークを言って"}],
    stream=True
)

# 結果をストリーミングして表示します
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
```

### Fletアプリ側のフロー
1. 画面左側にユーザとの会話が表示される。  
    例） 「Pythonのジョークを言って」
2. コパイロットが 「ふとんがふっとんだ」 と（面白くない）候補を出す。
3. オペレーターがそれを削除し、 「Pythonはニシキヘビですが、コードは締め付けません」 と書き直して 送信 ボタンを押す。
4. 画面左側の会話に送信したテキストが追加され、クライアント側には書き直されたジョークだけが届く。

