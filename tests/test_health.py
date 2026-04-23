import os
import asyncio
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer, TestClient
import importlib.util
from pathlib import Path

# Dynamically load the bot module (file is not in a Python package)
repo_root = Path(__file__).resolve().parents[1]
bot_path = repo_root / "telegram-bot" / "bot.py"
spec = importlib.util.spec_from_file_location("bot_module", str(bot_path))
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load bot module from {bot_path}")
bot_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot_module)


@pytest.mark.asyncio
async def test_health_and_ready(monkeypatch, aiohttp_unused_port):
    # Start a fake LLM server that responds 200 to POST
    async def llm_handler(request):
        data = await request.json()
        return web.json_response({"choices": [{"message": {"content": "pong"}}]})

    llm_app = web.Application()
    llm_app.router.add_post("/v1/chat/completions", llm_handler)

    port = aiohttp_unused_port()
    server = TestServer(llm_app, port=port)
    await server.start_server()

    try:
        # Point OLLAMA_API_URL to the fake server
        monkeypatch.setenv("OLLAMA_API_URL", f"http://127.0.0.1:{port}/v1/chat/completions")

        # Create the health app and run it in a TestServer
        health_app = bot_module.create_health_app()
        health_server = TestServer(health_app)
        await health_server.start_server()
        client = TestClient(health_server)
        await client.start_server()

        # /health should be ok
        resp = await client.get("/health")
        assert resp.status == 200
        text = await resp.text()
        assert text == "ok"

        # /ready should be ok because fake LLM replies 200
        resp = await client.get("/ready")
        assert resp.status == 200
        text = await resp.text()
        assert text == "ok"

    finally:
        await health_server.close()
        await server.close()
