from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from services.chatollama_service import stream_blog_from_ollama

app = FastAPI()

@app.websocket("/ws/generate-blog")
async def websocket_generate_blog(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        prompt = data.get("prompt")
        if not prompt:
            await websocket.send_json({"error": "Prompt is required."})
            await websocket.close()
            return
        async for chunk in stream_blog_from_ollama(prompt):
            await websocket.send_text(chunk)
        await websocket.close()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
