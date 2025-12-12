import json
import os
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# 環境変数 OPENAI_API_KEY が設定されていることを前提とします

# --- 1. Structured Output スキーマの定義 ---

class DraftResponse(BaseModel):
    """
    LLMが生成する返信候補の構造。
    返信として適切なものから順に draft1, draft2, draft3 に格納される。
    """
    draft1: str = Field(
        ..., 
        description="最も適切/推奨される返信案。全ての指示とコンテキストを最も自然に満たすもの。"
    )
    draft2: str = Field(
        ..., 
        description="2番目に適切な返信案。"
    )
    draft3: str = Field(
        ..., 
        description="3番目に適切な返信案。"
    )


# --- 2. ヘルパー関数群（前回のものから変更なし） ---

def process_inputs(inputs: Dict[str, Any]) -> Dict[str, str]:
    """
    入力辞書から必要な情報を抽出し、プロンプトに埋め込む文字列を生成します。
    """
    messages = inputs.get("messages", [])
    copilot_instruction = inputs.get("instruction", "")  # ユーザ入力の指示（任意）

    # A. 会話内システムプロンプトの抽出と履歴の分離
    inner_sys_content = "特になし（一般的なAIとして振る舞ってください）"
    history_msgs = []

    for m in messages:
        if isinstance(m, SystemMessage):
            # 会話内システムプロンプトとして扱う
            inner_sys_content = m.content
        else:
            history_msgs.append(m)

    # B. Copilot指示のデフォルト値処理
    formatted_instruction = copilot_instruction if copilot_instruction else "特になし"

    # C. 会話履歴のテキスト化
    formatted_history = ""
    for m in history_msgs:
        if isinstance(m, HumanMessage):
            formatted_history += f"User: {m.content}\n"
        elif isinstance(m, AIMessage):
            formatted_history += f"Assistant: {m.content}\n"
        
    return {
        "copilot_instruction": formatted_instruction,
        "inner_system_prompt": inner_sys_content,
        "formatted_history": formatted_history
    }


# --- 3. プロンプト定義の更新 ---

# LLMへの固定システムプロンプト（タスク定義）
SYSTEM_TEMPLATE = """あなたはチャットボットの返信作成支援AIです。
提供された情報に基づき、直近のユーザー発言に対する返信候補を3つ作成し、指定されたJSONスキーマに従って出力してください。

# 重要な指示
1. 返信は、draft1, draft2, draft3 に格納してください。以下に特に指定がない限り**最も適切であると判断したものから順に**格納してください。
2. 自身で考えた感想や付帯情報（例: 「これが最も適切です」など）は含めず、純粋な返信文のみを出力してください。
"""

# ユーザー入力部分（変数埋め込み）
HUMAN_TEMPLATE = """以下の情報を元に、返信を生成してください。

### 1. Copilotへの指示（今回の返信の方針）
{copilot_instruction}

### 2. キャラクター設定（会話全体の前提）
{inner_system_prompt}

### 3. 会話履歴
\"\"\"
{formatted_history}
\"\"\"

返信候補をJSON形式で出力してください:"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_TEMPLATE),
    ("human", HUMAN_TEMPLATE)
])


# --- 4. モデル・チェーン構築（Structured Outputの適用） ---

# モデルの初期化
model = ChatOpenAI(model="gpt-5.1", temperature=0.7)

# Structured Outputを適用したLLMインスタンスを作成
structured_llm = model.with_structured_output(DraftResponse)

# LCELチェーン
# process_inputs で辞書を作り、prompt に流し込む
chain_structured = (
    RunnableLambda(process_inputs)
    | prompt
    | structured_llm
)

# --- 5. 実行テスト ---

# ケース：Copilot指示と会話内システムプロンプトがある場合
print("--- Case: Structured Output Test (Full Context) ---")
inputs = {
    "instruction": "ここはあえて心配してないふりをして",
    "messages": [
        SystemMessage(content="あなたは友達AIです．ユーザとは旧知の仲で，心配性です．"),
        HumanMessage(content="昨日、駅前ですごい転び方しちゃってさ..."),
        AIMessage(content="マジかよ！大丈夫だったか？だぜ？"),
        HumanMessage(content="うん、恥ずかしかったけど怪我はなかったよ")
    ]
}

# 実行
try:
    result_obj: DraftResponse = chain_structured.invoke(inputs)

    print("\n[Python Object (DraftResponse)]")
    print(f"Type: {type(result_obj)}")
    print(f"draft1 (最も適切): {result_obj.draft1}")
    print(f"draft2: {result_obj.draft2}")
    print(f"draft3: {result_obj.draft3}")

    # JSONとして出力してみる
    print("\n[JSON Output]")
    print(json.dumps(result_obj.dict(), ensure_ascii=False, indent=2))

except Exception as e:
    print(f"エラーが発生しました。OpenAI APIキーが設定されているか確認してください: {e}")