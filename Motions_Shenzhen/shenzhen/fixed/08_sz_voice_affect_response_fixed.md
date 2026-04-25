# `sz_voice_affect_response` 固定动作实现指导

## 当前目标

先做一版“导演台可选分支”的语音情绪反馈，不依赖实时 ASR/意图识别。

## 配套蓝图

如果需要更具体到“开心 / praise 这类正向反应脚本该怎么分段写”，继续看：

- [08_sz_happy_reaction_script_blueprint.md](./08_sz_happy_reaction_script_blueprint.md)

那份文档把：

- `08_20260425_043832_01.mp4`
- `Mira Light 展位交互方案 副本.pdf` 后半段补充交互里的“开心”

压成了一份固定动作优先的脚本设计草案。

## 固定版实现原则

- 不让系统自己判断 intent
- 由导演台或主持人手动指定分支
- 先把 `tired / praise / criticism` 三条固定动作版本做出来

## 优先复用的板端脚本

- `servo_2_nod_1900_2200.py`
- `servo_3_shake_2100_2000.py`
- `servo_1_2_dodge_1848_1808.py`
- 灯头 `ALL / BREATHE / BRI / WAKE / SPIN`

## 第一版推荐分支

### tired

- 暖呼吸
- 小幅低头 / 点头

### praise

- 更亮一点
- 轻快点头

### criticism

- 略暗
- 轻摇头或轻后缩

## 当前固定版能证明什么

它能证明：

- 不同输入语义可以映射到不同输出风格

它不能证明：

- Mira 已经真的实时听懂了这句话

## 后续升级方向

第二版再把：

- `transcript`
- `intent`
- `valence`

接到 builder 或事件桥里。
