"""
/v1/chat/completions APIリクエストを処理するサーバー
"""

import asyncio
import json
import threading
import time
from typing import AsyncGenerator, Awaitable, Callable, List, Optional

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

# 同じディレクトリにある api_model.py からインポート
# フォルダ構成が異なる場合（例: modelフォルダ内にある場合）は適宜修正してください
from model.api_model import (
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionRequestMessage,
    ChatCompletionResponseMessage,
    ChatCompletionStreamChoice,
    ChatCompletionStreamResponseDelta,
    CreateChatCompletionRequest,
    CreateChatCompletionResponse,
    FinishReason,
)

# ==========================================
# Server Management Class
# ==========================================


class FastAPIServer:
    def __init__(
        self,
        host: str,
        port: int,
        log_level: str,
        on_message_received: Callable[[Awaitable[ChatCompletionRequestMessage]], str],
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
    ):
        self.app = FastAPI(
            title="Human Chat Completions",
            summary="OpenAI Chat Completions API compatible API.",
            description="Human Chat Completions is a simple HTTP server that implements the OpenAI Chat Completions API.",
            version="0.1.0",
        )
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.app.add_api_route(
            "/",
            self.root,
            methods=["GET"],
        )
        self.app.add_api_route(
            "/v1/chat/completions",
            self.chat_completions,
            methods=["POST"],
        )
        self.app.add_exception_handler(404, self.not_found_handler)
        self.config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level=log_level,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            loop="asyncio",
        )
        self.server = uvicorn.Server(self.config)
        self._thread = None
        self.on_message_received = on_message_received

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        def target():
            # スレッド内で新しいイベントループを作成・設定
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.server.run()

        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0):
        if self.server.started:
            self.server.should_exit = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout)
            if self._thread.is_alive():
                print("Warning: Uvicorn thread did not exit gracefully.")

    # ==========================================
    # Mock Business Logic (To be separated later)
    # ==========================================

    async def get_response_content(self, messages: List[ChatCompletionRequestMessage]) -> str:
        """
        ここにビジネスロジック（人間への通知、DB参照など）が入ります。
        現在は固定のレスポンスを返します。
        """
        # 実際にはここでユーザー入力を待機する処理が入る想定
        # await wait_for_human_input(...)

        # 擬似的な遅延（思考時間や入力待ち）
        await asyncio.sleep(1.0)

        # モックの固定レスポンス
        return "これはHuman Backendからの固定レスポンスです。UIやビジネスロジックが接続されると、ここにオペレータの入力が反映されます。"


    # ==========================================
    # Streaming Generator
    # ==========================================


    async def stream_generator(self, content: str, model_id: str) -> AsyncGenerator[str, None]:
        """
        Server-Sent Events (SSE) 形式でレスポンスをストリーミングします。
        """
        chunk_id = f"chatcmpl-{int(time.time())}"
        created_time = int(time.time())

        # 文字単位でストリーミングするシミュレーション
        tokens = list(content)

        for i, token in enumerate(tokens):
            # 擬似的なタイピング遅延
            await asyncio.sleep(0.05)

            chunk = ChatCompletionChunk(
                id=chunk_id,
                created=created_time,
                model=model_id,
                choices=[
                    ChatCompletionStreamChoice(
                        index=0,
                        delta=ChatCompletionStreamResponseDelta(
                            # 最初のチャンクだけroleを入れる（仕様上は毎回でも可だが、一般的実装に合わせる）
                            role="assistant" if i == 0 else None,
                            content=token,
                        ),
                        finish_reason=None,
                    )
                ],
            )

            # SSE形式: data: <json_string>\n\n
            yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"

        # 完了時のChunk (finish_reason="stop", contentは空)
        final_chunk = ChatCompletionChunk(
            id=chunk_id,
            created=created_time,
            model=model_id,
            choices=[
                ChatCompletionStreamChoice(
                    index=0,
                    delta=ChatCompletionStreamResponseDelta(),
                    finish_reason=FinishReason.stop,
                )
            ],
            # usageを送る場合はここに `usage=...` を追加
        )
        yield f"data: {final_chunk.model_dump_json(exclude_none=True)}\n\n"

        # ストリーム終了シグナル
        yield "data: [DONE]\n\n"


    # ==========================================
    # Endpoints
    # ==========================================


    async def root(self):
        return {"message": "Human Chat Completions listening on port 8080"}


    async def chat_completions(
        self,
        request: CreateChatCompletionRequest,
        authorization: Optional[str] = Header(None),
    ):
        """
        OpenAI互換のChat Completionsエンドポイント
        """
        # 1. 応答内容の取得（ビジネスロジック呼び出し）
        # ストリーミングの場合でも、現状は「全応答が決まってから流す」方式としています
        print(request.messages)
        response_content = await self.on_message_received(request.messages)

        # モデルIDの取得
        model_id = request.model

        # 2. ストリーミングリクエストの場合
        if request.stream:
            return StreamingResponse(
                self.stream_generator(response_content, model_id), media_type="text/event-stream"
            )

        # 3. 通常リクエストの場合
        else:
            return CreateChatCompletionResponse(
                id=f"chatcmpl-{int(time.time())}",
                created=int(time.time()),
                model=model_id,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatCompletionResponseMessage(
                            role="assistant", content=response_content
                        ),
                        finish_reason=FinishReason.stop,
                    )
                ],
            )
    
    async def not_found_handler(self, request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": "Human Chat Completions supports only POST /v1/chat/completions endpoint.",
            },
        )
