# Mira Light 最简接收器 ESP32 调用示例

## 1. 启动接收器

在电脑上运行：

```bash
python3 scripts/simple_lamp_receiver.py
```

如果你想显式指定保存目录：

```bash
python3 scripts/simple_lamp_receiver.py \
  --host 0.0.0.0 \
  --port 9784 \
  --save-root /Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver
```

## 2. 单片机先测健康检查

如果电脑 IP 是 `172.20.10.2`，单片机先访问：

```text
GET http://172.20.10.2:9784/health
```

预期收到：

```json
{
  "ok": true
}
```

## 3. 状态上报示例

这是最推荐先实现的第一条接口。

### curl 示例

```bash
curl --location 'http://172.20.10.2:9784/device/status' \
--header 'Content-Type: application/json' \
--data '{
  "deviceId": "mira-light-001",
  "scene": "wake_up",
  "playing": true,
  "servo1": 90,
  "servo2": 96,
  "servo3": 98,
  "servo4": 90,
  "ledMode": "solid",
  "brightness": 130
}'
```

### 更完整版本

```bash
curl --location 'http://172.20.10.2:9784/device/status' \
--header 'Content-Type: application/json' \
--data '{
  "deviceId": "mira-light-001",
  "scene": "wake_up",
  "playing": true,
  "servos": [
    {"name":"servo1","angle":90,"pin":18},
    {"name":"servo2","angle":96,"pin":13},
    {"name":"servo3","angle":98,"pin":14},
    {"name":"servo4","angle":90,"pin":15}
  ],
  "led": {
    "mode":"solid",
    "brightness":130,
    "color":{"r":255,"g":220,"b":180}
  }
}'
```

## 4. 上传图片示例

如果单片机能直接发送二进制内容，推荐使用：

### curl 示例

```bash
curl --location 'http://172.20.10.2:9784/device/upload?deviceId=mira-light-001&fileName=frame.jpg&category=images' \
--header 'Content-Type: image/jpeg' \
--data-binary @frame.jpg
```

或者把设备信息放到 header 里：

```bash
curl --location 'http://172.20.10.2:9784/device/upload' \
--header 'X-Device-Id: mira-light-001' \
--header 'X-File-Name: frame.jpg' \
--header 'X-File-Category: images' \
--header 'Content-Type: image/jpeg' \
--data-binary @frame.jpg
```

## 5. 上传 Base64 图片示例

如果单片机侧更方便先转成 Base64，再发 JSON，可以使用：

```bash
curl --location 'http://172.20.10.2:9784/device/upload-base64' \
--header 'Content-Type: application/json' \
--data '{
  "deviceId": "mira-light-001",
  "fileName": "frame.jpg",
  "category": "images",
  "contentType": "image/jpeg",
  "contentBase64": "<base64内容>"
}'
```

## 6. 保存后会出现什么文件

### 状态快照

```text
~/Documents/Mira-Light-Runtime/simple-receiver/snapshots/mira-light-001.latest.json
```

### 事件日志

```text
~/Documents/Mira-Light-Runtime/simple-receiver/events/2026-04-08.jsonl
```

### 上传图片

```text
~/Documents/Mira-Light-Runtime/simple-receiver/uploads/2026-04-08/mira-light-001/images/frame.jpg
```

### 上传图片元数据

```text
~/Documents/Mira-Light-Runtime/simple-receiver/uploads/2026-04-08/mira-light-001/images/frame.jpg.meta.json
```

## 7. 推荐的单片机发送顺序

最简单、最稳的顺序建议是：

1. 开机后先调用 `/health`
2. 每隔几秒调用 `/device/status`
3. 需要上传图片时调用 `/device/upload` 或 `/device/upload-base64`

## 8. 当前阶段最推荐做法

如果现在只想先把链路打通，我建议你先只做这两件事：

1. 实现 `/device/status`
2. 再实现 `/device/upload`

因为这样最容易排查，也最符合当前 `ESP32 智能台灯.pdf` 已有能力范围。

