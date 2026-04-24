"""
图像接收端脚本 - 在 Windows 上运行
启动 HTTP 服务器接收 RDK X5 发来的 JPEG 帧并实时显示
用法: python cam_receiver.py [端口]
"""
import sys
import threading
import numpy as np
import cv2
from http.server import HTTPServer, BaseHTTPRequestHandler

latest_frame = None
frame_lock = threading.Lock()
frame_count = 0


class FrameHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global latest_frame, frame_count
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self.send_response(400)
            self.end_headers()
            return

        data = self.rfile.read(length)
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        if img is not None:
            with frame_lock:
                latest_frame = img
                frame_count += 1

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, fmt, *args):
        seq = self.headers.get("X-Seq", "?")
        print(f"  [recv] seq={seq}  size={self.headers.get('Content-Length', '?')} bytes")


def run_server(port):
    server = HTTPServer(("0.0.0.0", port), FrameHandler)
    print(f"HTTP 服务器监听 0.0.0.0:{port} ...")
    server.serve_forever()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    t = threading.Thread(target=run_server, args=(port,), daemon=True)
    t.start()

    print("等待接收图像... (按 q 退出窗口)")

    while True:
        with frame_lock:
            frame = latest_frame.copy() if latest_frame is not None else None
            cnt = frame_count

        if frame is not None:
            info = f"frames: {cnt}"
            cv2.putText(frame, info, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("RDK X5 Camera Stream", frame)

        key = cv2.waitKey(30) & 0xFF
        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    print(f"退出，共接收 {frame_count} 帧")


if __name__ == "__main__":
    main()
