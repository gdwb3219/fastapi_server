# app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 하드코딩된 방 코드
HARDCODED_ROOM_CODE = "myroom123"

rooms = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, room_code: str):
        await websocket.accept()
        if room_code not in rooms:
            rooms[room_code] = []
        rooms[room_code].append(websocket)

    def disconnect(self, websocket: WebSocket, room_code: str):
        rooms[room_code].remove(websocket)
        if not rooms[room_code]:
            del rooms[room_code]

    async def broadcast(self, message: str, room_code: str):
        for connection in rooms.get(room_code, []):
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    if room_code != HARDCODED_ROOM_CODE:
        await websocket.close()
        return
    await manager.connect(websocket, room_code)
    try:
        while True:
            data = await websocket.receive_text()
            # Offer나 Answer 정보가 도착했는지 확인하기 위해 메시지를 출력합니다.
            print(f"Received message in room {room_code}: {data}")

            # Offer나 Answer 정보인 경우 확인
            if "offer" in data.lower():
                print(f"Received offer: {data}")
            elif "answer" in data.lower():
                print(f"Received answer: {data}")

            await manager.broadcast(data, room_code)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_code)

class RoomCodeRequest(BaseModel):
    room_code: str

@app.post("/validate-room-code")
async def validate_room_code(request: RoomCodeRequest):
    if request.room_code == HARDCODED_ROOM_CODE:
        return {"valid": True}
    else:
        raise HTTPException(status_code=400, detail="Invalid room code")
