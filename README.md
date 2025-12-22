# <img src="https://github.com/kei-mag/human-chat-completions/blob/main/src/assets/icon.png?raw=true" height="50" style="vertical-align: bottom;"> Human Chat Completions

&thinsp; **日本語** / [English](README_en.md) &emsp;&emsp; [![Release](https://github.com/miyamoto-hai-lab/human-chat-completions/actions/workflows/release.yml/badge.svg)](https://github.com/miyamoto-hai-lab/human-chat-completions/actions/workflows/release.yml)

Human Chat Completions は、[Flet](https://flet.dev)で構築された オズの魔法使い法 (Wizard of Oz) 実験用のデスクトップチャットアプリケーションです。

![Preview Clip](preview_clip.gif)

OpenAIの [`v1/chat/completions` API](https://platform.openai.com/docs/api-reference/chat/create)と互換性のあるエンドポイントを提供しますが、リクエストは自動処理されず、Flet製のチャット画面（オペレーターUI）に転送されます。

最大の特徴は 「**LLMコパイロット（応答候補生成）**」機能 です。バックグラウンドで本物のLLMがドラフトを作成し、人間のオペレーターはそれを 編集・修正・承認 してからクライアントに送信できます。これにより、ゼロから返信を書く負担を減らしつつ、正確なコントロールが可能になります。

基本はすべてLLMに応答させ、人間による介入が必要になった場合のみ、介入することもできます。
これにより、**「完全な人間による応答」「AIドラフトの修正」「完全自動のAI応答」を状況に応じて自由に切り替えることが可能**です。

## 主な特徴
- **API完全互換**: 既存のチャットアプリの接続先 (base_url) を変えるだけで、AI応答から人間介入型へ切り替え可能。
- **ストリーミング対応**: `stream: true` に対応。多くの一般的なOpen AIクライアントでも正常に動作します。
- **Flet GUI**: Pythonだけで記述されているので、自動応答プログラムを作成して連携するのも比較的簡単に行えます。
- **LLM Copilot**:
    - ユーザーの問いに対し、まずは内部のLLMが「下書き」を生成。オペレーターはその下書きを採用するか、修正して送信するかを選択可能です。
    - Copilotには「無効」，「下書きを作成」，「自動応答」の3種類があり、いつでも切り替えられるので様々な実験に柔軟に対応できます。
- **ログ収集**: 「ユーザー入力」「AIのドラフト」「人間が修正した最終回答」の3点を記録し、実験記録として役立てることができます。

## 利用シーン
1. **WoZ法によるプロトタイピング**: 開発初期段階で、理想的なAIの挙動を人間が演じて検証する。
2. **RLHF用データ作成**: AIの回答を人間がリアルタイムで修正し、高品質な学習データを作成する。
3. **リスク管理**: センシティブな話題に対して、オペレーターが介入して安全な回答に書き換える。

## 使い方
### インストールと起動
[最新のRelease](https://github.com/miyamoto-hai-lab/human-chat-completions/releases/latest)からお使いのOSの実行ファイルをダウンロードします．
Windowsの場合はインストーラーとなっているので，ウィザードに沿ってインストールしてください．

>[!NOTE]
>このアプリケーションは署名がされていないため、インストール時・起動時にセキュリティ警告が出る場合がありますが、安全なアプリですので許可していただきますようお願いいたします。


### クライアント
Open AI Completions APIに対応したクライアントアプリであれば使用可能です。
APIのエンドポイントURLにHuman Chat Completionsサーバのアドレスを，APIキーには任意の文字列を設定してください。
Human Chat Completionsサーバのアドレスは，アプリ左上に記載されています。

クライアントアプリは以下の2つはテスト済みです。
- [Chatbox AI](https://chatboxai.app/ja) (iOS版，Windows版)  
    1. 設定から「モデルプロバイダーを追加」を押し、「OpenAI API互換」モードで追加します。
    2. APIキーの欄には任意の文字列を入れ、APIホストにはHuman Chat Completionsサーバのアドレスを、APIパスには`/v1/chat/completions`を設定します。
    3. 上記が正しく設定されている場合、モデル取得ボタンを押すと`Huamn`モデルが取得されます。Chat時にはこのモデルを指定してください。
- [Jan](https://www.jan.ai/) (Windows版)  
    1. 設定の「モデルプロバイダー」からプロバイダーを追加します。
    2. APIキーの欄には任意の文字列を入れ、Base URLには`<Human Chat Completionsサーバのアドレス>/v1`を設定します。
    3. 上記が正しく設定されている場合、モデル更新ボタンを押すと`Huamn`モデルが取得されます。Chat時にはこのモデルを指定してください。

また、宮本研究室で開発している[Chat UI](https://github.com/miyamoto-hai-lab/chat-ui)でも利用可能です。  
`provider: "openai"`，`endpoint_url: <Human Chat Completionsサーバのアドレス>/v1/chat/completions`を設定してください。

もちろん、Python等のプログラムからHuman Chat Completionsにリクエストを送ることも可能です。

#### Pythonでのコード例
```python
from openai import OpenAI

client = OpenAI(
    api_key="dummy",  # APIキーはダミーでOK
    base_url="http://localhost:8000/v1/chat/completions"  # サーバーのアドレスを指定
)

# リクエストを送信すると、Fletの画面に着信します
stream = client.chat.completions.create(
    model="human",  # 任意でOKですが GET /v1/chat/models では "human" というモデルを返します
    messages=[{"role": "user", "content": "Pythonのジョークを言って"}],
    stream=True
)

# 結果をストリーミングして表示します
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
```

[langchain](https://www.langchain.com/)等でも簡単に利用できます。
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(
    model="human",  # 接続先で有効なモデル名を指定
    base_url="http://localhost:8000/v1/chat/completions",  # サーバーのアドレスを指定
    api_key="dummy" # APIキーはダミーでOK
)

messages = [("system", "あなたは親切なAIアシスタントです。ユーザに共感的な会話を心がけてください。")]

while True:
    user_message = input("You: ")
    messages.append(("human", user_message))
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | model | StrOutputParser
    ai_message = chian.invoke({})
    messages.append(("assistant", ai_message))
    print(f"AI: {ai_message}")
```

### オペレーター側のフロー
0. 左上の [**STOPPED**] ボタンを押してサーバーをスタートさせます。
1. 画面左側にユーザとの会話が表示されます。  
    例） 「「プレミアムプランを解約したいのですが、日割り計算になりますか？」
2. LLMドラフトモードの場合、コパイロットが 3つ候補を出します。  
    例） 「お問い合わせありがとうございます。プレミアムプランの解約ですね。はい、解約月は日割り計算となります。」 ← 間違いを含んでいる
3. オペレーターは生成されたドラフトを、必要に応じて修正してから 送信 ボタンを押す。  
    例） 「お問い合わせありがとうございます。プレミアムプランの解約ですね。**大変恐縮ですが、現在の利用規約では日割り計算は行われず、解約日まで全額が発生いたします。**」
4. 画面左側の会話に送信したテキストが追加され、クライアント側には3で送信した最終的な返答文が届く。
