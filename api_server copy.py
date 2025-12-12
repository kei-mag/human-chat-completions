"""
/v1/chat/completions APIリクエストを処理するサーバー
"""
import asyncio
import threading
from time import time
from typing import AsyncGenerator, Optional

import httpx
import uvicorn
from fastapi import FastAPI, Header, NotFound
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from model.api_model import (
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionResponseMessage,
    ChatCompletionStreamChoice,
    ChatCompletionStreamResponseDelta,
    CreateChatCompletionRequest,
    CreateChatCompletionResponse,
    FinishReason,
)

app = FastAPI(
    title="Human Chat Completions",
    summary="OpenAI Chat Completions API compatible API.",
    description="Human Chat Completions is a simple HTTP server that implements the OpenAI Chat Completions API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return "Human Chat Completions listening on port 8080"


@app.get("*", include_in_schema=False)
async def catch_all():
    return NotFound(
        "Human Chat Completions supports only POST /v1/chat/completions endpoint."
    )


@app.post("/v1/chat/completions")
async def chat_completions(request: CreateChatCompletionRequest, authorization: Optional[str] = Header(None)):
    """
    OpenAI互換のChat Completionsエンドポイント
    """
    # 1. 応答内容の決定（人間入力の待機など）
    # ストリーミングの場合は応答内容が決まってから流す
    response_content = "これはテストです" # 後で実装するのでこのまま

    # 2. ストリーミングリクエストの場合
    if request.stream:
        return StreamingResponse(
            stream_generator(response_content, request.model),
            media_type="text/event-stream"
        )

    # 3. 通常リクエストの場合
    else:
        return CreateChatCompletionResponse(
            id=f"chatcmpl-{int(time())}",
            created=int(time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatCompletionResponseMessage(
                        role="assistant",
                        content=response_content
                    ),
                    finish_reason=FinishReason.stop
                )
            ]
        )

async def stream_generator(
    content: str, 
    model_id: str
) -> AsyncGenerator[str, None]:
    """
    Server-Sent Events (SSE) 形式でレスポンスをストリーミングします。
    OpenAIの仕様に従い、`data: {json}\n\n` を送信します。
    """
    chunk_id = f"chatcmpl-{int(time())}"
    created_time = int(time())

    # 人間がタイピングしているような演出のために、文字ごとに分割して送信
    tokens = list(content)

    for i, token in enumerate(tokens):
        # 少し待機（タイピング速度のシミュレーション）
        await asyncio.sleep(0.05)

        chunk = ChatCompletionChunk(
            id=chunk_id,
            created=created_time,
            model=model_id,
            choices=[
                ChatCompletionStreamChoice(
                    index=0,
                    delta=ChatCompletionStreamResponseDelta(
                        # 最初のチャンク、または必要に応じてroleを含める
                        role="assistant" if i == 0 else None,
                        content=token
                    ),
                    finish_reason=None
                )
            ]
        )
        
        # SSE形式: data: <json_string>\n\n
        yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"

    # 完了時のChunk (finish_reason="stop")
    final_chunk = ChatCompletionChunk(
        id=chunk_id,
        created=created_time,
        model=model_id,
        choices=[
            ChatCompletionStreamChoice(
                index=0,
                delta=ChatCompletionStreamResponseDelta(), # 内容は空
                finish_reason=FinishReason.stop
            )
        ]
    )
    yield f"data: {final_chunk.model_dump_json(exclude_none=True)}\n\n"
    
    # ストリーム終了シグナル
    yield "data: [DONE]\n\n"


class FastAPIServer:
    def __init__(self, app, host="0.0.0.0", port=8080, log_level="info"):
        self.config = uvicorn.Config(app, host=host, port=port, log_level=log_level)
        self.server = uvicorn.Server(self.config)
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        def target():
            asyncio.set_event_loop(asyncio.new_event_loop())
            self.server.run()  # ブロッキング処理

        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0):
        if self._thread and self._thread.is_alive():
            self.server.should_exit = True  # Uvicornサーバーを停止する
            self._thread.join(timeout)  # Uvicornスレッドが終了するまで待機
            if self._thread.is_alive():
                print("Warning: Uvicorn thread did not exit gracefully.")
                self._thread.raise_exception(
                    KeyboardInterrupt
                )  # Uvicornスレッドを強制的に停止する

    def is_running(self):
        return self._thread and self._thread.is_alive()


if __name__ == "__main__":
    server = FastAPIServer(app)
    print(f"{server.is_running()=}")
    input("Enterでサーバー起動")
    server.start()
    
    print(f"{server.is_running()=}")
    input("Enterでサーバー停止")
    server.stop()
    print(f"{server.is_running()=}")
