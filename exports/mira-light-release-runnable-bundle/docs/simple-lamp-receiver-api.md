# Mira Light 最简接收器 API 说明

## 基地址

假设接收器运行在本机电脑上，默认推荐地址为：

```text
http://<电脑局域网IP>:9784
```

例如：

```text
http://172.20.10.2:9784
```

## 1. 健康检查

### 请求

```http
GET /health
```

### 返回示例

```json
{
  "ok": true,
  "service": "simple-lamp-receiver",
  "saveRoot": "/Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver",
  "uploadsRoot": "/Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver/uploads",
  "time": "2026-04-08T12:00:00+08:00"
}
```

### 用途

- 检查 server 是否在线
- 检查保存目录是否已建立

## 2. 状态上报

### 请求

```http
POST /device/status
Content-Type: application/json
```

### 建议请求体

```json
{
  "deviceId": "mira-light-001",
  "scene": "wake_up",
  "playing": true,
  "servo1": 90,
  "servo2": 96,
  "servo3": 98,
  "servo4": 90,
  "ledMode": "solid",
  "brightness": 130
}
```

### 也可以上传更完整结构

```json
{
  "deviceId": "mira-light-001",
  "scene": "wake_up",
  "playing": true,
  "servos": [
    {"name": "servo1", "angle": 90, "pin": 18},
    {"name": "servo2", "angle": 96, "pin": 13},
    {"name": "servo3", "angle": 98, "pin": 14},
    {"name": "servo4", "angle": 90, "pin": 15}
  ],
  "led": {
    "mode": "solid",
    "brightness": 130,
    "color": {"r": 255, "g": 220, "b": 180}
  }
}
```

### 返回示例

```json
{
  "ok": true,
  "saved": true,
  "deviceId": "mira-light-001",
  "snapshotPath": "/Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver/snapshots/mira-light-001.latest.json",
  "eventPath": "/Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver/events/2026-04-08.jsonl"
}
```

### 保存行为

收到状态后会自动：

1. 覆盖保存最新快照到 `snapshots/`
2. 追加一条 JSONL 记录到 `events/`

## 3. 二进制文件上传

### 请求

```http
POST /device/upload
```

### 推荐 Header

```http
X-Device-Id: mira-light-001
X-File-Name: frame.jpg
X-File-Category: images
Content-Type: image/jpeg
```

### 也可以通过 query 传递

```text
/device/upload?deviceId=mira-light-001&fileName=frame.jpg&category=images
```

### Body

请求体直接放原始二进制内容。

### 返回示例

```json
{
  "ok": true,
  "saved": true,
  "deviceId": "mira-light-001",
  "path": "/Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver/uploads/2026-04-08/mira-light-001/images/frame.jpg",
  "metaPath": "/Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver/uploads/2026-04-08/mira-light-001/images/frame.jpg.meta.json",
  "eventPath": "/Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver/events/2026-04-08.jsonl"
}
```

## 4. Base64 文件上传

### 请求

```http
POST /device/upload-base64
Content-Type: application/json
```

### 请求体

```json
{
  "deviceId": "mira-light-001",
  "fileName": "frame.jpg",
  "category": "images",
  "contentType": "image/jpeg",
  "contentBase64": "<base64内容>"
}
```

### 返回示例

```json
{
  "ok": true,
  "saved": true,
  "deviceId": "mira-light-001",
  "path": "/Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver/uploads/2026-04-08/mira-light-001/images/frame.jpg",
  "metaPath": "/Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver/uploads/2026-04-08/mira-light-001/images/frame.jpg.meta.json",
  "eventPath": "/Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver/events/2026-04-08.jsonl"
}
```

## 文件保存规则

### 状态

```text
~/Documents/Mira-Light-Runtime/simple-receiver/snapshots/<deviceId>.latest.json
```

### 日志

```text
~/Documents/Mira-Light-Runtime/simple-receiver/events/YYYY-MM-DD.jsonl
```

### 上传文件

```text
~/Documents/Mira-Light-Runtime/simple-receiver/uploads/YYYY-MM-DD/<deviceId>/<category>/<fileName>
```

### 上传文件元数据

```text
同名文件 + .meta.json
```

## 推荐字段规范

### deviceId

推荐始终带上：

```text
mira-light-001
```

### category

建议统一用这些：

- `images`
- `captures`
- `logs`
- `misc`

### fileName

建议带扩展名，例如：

- `frame-0001.jpg`
- `event-log.txt`

## 当前适用范围

这套 API 适合当前阶段：

- 先收状态
- 先收图片
- 先做本机调试记录

它是“最小可用接收器”，不是完整 release API。

