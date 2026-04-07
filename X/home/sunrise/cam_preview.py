"""
USB 摄像头预览脚本 - 在 RDK X5 上运行
按 q 退出预览窗口
"""
import cv2
import sys


def main():
    dev = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    cap = cv2.VideoCapture(dev)
    if not cap.isOpened():
        print(f"[ERROR] 无法打开摄像头 /dev/video{dev}")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print(f"摄像头已打开: /dev/video{dev}  按 q 退出")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] 读取帧失败，跳过")
            continue
        cv2.imshow("USB Camera Preview", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
