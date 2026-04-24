"""
摄像头抓图 + HTTP 发送脚本 - 在 RDK X5 上运行
每秒抓取 10 帧，将 JPEG 二进制通过 HTTP POST 发送到指定地址
用法: python3 cam_sender.py <接收端IP> [端口] [摄像头编号]
"""
import cv2
import sys
import time
import urllib.request


def main():
    if len(sys.argv) < 2:
        print("用法: python3 cam_sender.py <接收端IP> [端口] [摄像头编号]")
        print("示例: python3 cam_sender.py 192.168.1.100 8000 0")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    dev  = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    url = f"http://{host}:{port}/upload"

    cap = cv2.VideoCapture(dev)
    if not cap.isOpened():
        print(f"[ERROR] 无法打开摄像头 /dev/video{dev}")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    interval = 1.0 / 10  # 10 FPS
    seq = 0
    print(f"开始抓图并发送到 {url}  (Ctrl+C 退出)")

    try:
        while True:
            t0 = time.monotonic()
            ret, frame = cap.read()
            if not ret:
                continue

            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ok:
                continue

            data = buf.tobytes()
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "image/jpeg",
                    "X-Timestamp": str(time.time()),
                    "X-Seq": str(seq),
                },
                method="POST",
            )
            try:
                urllib.request.urlopen(req, timeout=2)
                seq += 1
                if seq % 10 == 0:
                    print(f"  已发送 {seq} 帧")
            except Exception as e:
                print(f"[WARN] 发送失败: {e}")

            elapsed = time.monotonic() - t0
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print(f"\n停止，共发送 {seq} 帧")
    finally:
        cap.release()


if __name__ == "__main__":
    main()
