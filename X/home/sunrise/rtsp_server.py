"""
RTSP 推流服务器 - 在 RDK X5 上运行
自动探测摄像头能力, 兼容 MJPEG / RAW 摄像头, 自动回退编码器
用法: python3 rtsp_server.py [摄像头编号] [端口] [挂载路径]
示例: python3 rtsp_server.py 0 8554 /cam
"""
import sys
import subprocess
import shutil

import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")
from gi.repository import Gst, GstRtspServer, GLib

Gst.init(None)


def check_gst_plugin(element_name):
    """检查某个 GStreamer 元素是否可用"""
    factory = Gst.ElementFactory.find(element_name)
    return factory is not None


def probe_camera_formats(device):
    """用 v4l2-ctl 探测摄像头支持的格式"""
    formats = {"mjpeg": False, "yuyv": False, "h264": False}
    widths = []
    try:
        out = subprocess.check_output(
            ["v4l2-ctl", "-d", device, "--list-formats-ext"],
            stderr=subprocess.STDOUT, text=True, timeout=5
        )
        lower = out.lower()
        if "mjpeg" in lower or "motion-jpeg" in lower:
            formats["mjpeg"] = True
        if "yuyv" in lower:
            formats["yuyv"] = True
        if "h264" in lower or "h.264" in lower:
            formats["h264"] = True
        for line in out.splitlines():
            line = line.strip()
            if "Size:" in line:
                parts = line.split()
                for p in parts:
                    if "x" in p and p[0].isdigit():
                        try:
                            w, h = p.split("x")
                            widths.append((int(w), int(h)))
                        except ValueError:
                            pass
    except Exception as e:
        print(f"  [WARN] v4l2-ctl 探测失败: {e}")
    return formats, sorted(set(widths))


def pick_resolution(sizes, preferred=(640, 480)):
    """从摄像头支持的分辨率中挑选"""
    if not sizes:
        return preferred
    if preferred in sizes:
        return preferred
    for w, h in sizes:
        if w >= 320 and h >= 240:
            return (w, h)
    return sizes[0]


def find_encoder():
    """按优先级查找可用的 H.264 编码器"""
    candidates = [
        ("x264enc", "x264enc tune=zerolatency bitrate=2000 speed-preset=ultrafast",
         "video/x-h264,profile=baseline"),
        ("openh264enc", "openh264enc bitrate=2000000 complexity=low",
         "video/x-h264,profile=baseline"),
        ("avenc_h264_omx", "avenc_h264_omx bitrate=2000000",
         "video/x-h264"),
    ]
    for name, enc_str, caps in candidates:
        if check_gst_plugin(name):
            print(f"  编码器: {name}")
            return enc_str, caps
    return None, None


def build_pipeline(device, width, height, fps, cam_formats):
    """根据摄像头能力和可用编码器构建管道"""
    enc_str, enc_caps = find_encoder()

    # 如果摄像头直接输出 H.264 (某些摄像头支持), 直接打包
    if cam_formats.get("h264"):
        pipeline = (
            f"( v4l2src device={device} ! "
            f"video/x-h264,width={width},height={height},framerate={fps}/1 ! "
            f"h264parse ! "
            f"rtph264pay name=pay0 pt=96 config-interval=1 )"
        )
        print(f"  模式: 摄像头原生 H.264 直出")
        return pipeline

    if enc_str is None:
        print("[ERROR] 找不到任何可用的 H.264 编码器!")
        print("  请安装: sudo apt install gstreamer1.0-plugins-ugly")
        print("  或:     sudo apt install gstreamer1.0-plugins-bad")
        sys.exit(1)

    # 优先用 MJPEG 源 (带宽小, USB 传输快), 再解码转编
    if cam_formats.get("mjpeg"):
        pipeline = (
            f"( v4l2src device={device} ! "
            f"image/jpeg,width={width},height={height},framerate={fps}/1 ! "
            f"jpegdec ! videoconvert ! video/x-raw,format=I420 ! "
            f"{enc_str} ! {enc_caps} ! "
            f"rtph264pay name=pay0 pt=96 config-interval=1 )"
        )
        print(f"  模式: MJPEG 解码 -> H.264 编码")
        return pipeline

    # RAW (YUYV 等) 源
    pipeline = (
        f"( v4l2src device={device} ! "
        f"video/x-raw,width={width},height={height},framerate={fps}/1 ! "
        f"videoconvert ! video/x-raw,format=I420 ! "
        f"{enc_str} ! {enc_caps} ! "
        f"rtph264pay name=pay0 pt=96 config-interval=1 )"
    )
    print(f"  模式: RAW -> H.264 编码")
    return pipeline


def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"


def main():
    dev_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    port    = sys.argv[2] if len(sys.argv) > 2 else "8554"
    mount   = sys.argv[3] if len(sys.argv) > 3 else "/cam"
    device  = f"/dev/video{dev_idx}"

    print(f"=== RTSP Server 启动 ===")
    print(f"  设备: {device}")

    # 探测
    cam_formats, sizes = probe_camera_formats(device)
    print(f"  摄像头格式: { {k:v for k,v in cam_formats.items() if v} }")
    if sizes:
        print(f"  可用分辨率: {sizes}")
    width, height = pick_resolution(sizes)
    fps = 25
    print(f"  选用: {width}x{height} @ {fps}fps")

    # 检查可用编码器
    avail = []
    for name in ["x264enc", "openh264enc", "avenc_h264_omx", "jpegdec", "videoconvert"]:
        if check_gst_plugin(name):
            avail.append(name)
    print(f"  可用插件: {avail}")

    launch = build_pipeline(device, width, height, fps, cam_formats)
    print(f"  管道: {launch}")

    server = GstRtspServer.RTSPServer()
    server.set_service(port)

    factory = GstRtspServer.RTSPMediaFactory()
    factory.set_launch(launch)
    factory.set_shared(True)

    mounts = server.get_mount_points()
    mounts.add_factory(mount, factory)
    server.attach(None)

    local_ip = get_local_ip()
    print()
    print(f"  RTSP 就绪: rtsp://{local_ip}:{port}{mount}")
    print(f"  Ctrl+C 退出")

    try:
        GLib.MainLoop().run()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()
