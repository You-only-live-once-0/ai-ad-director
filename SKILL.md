---
name: ai-ad-director
description: 用现有 AI 广告 Pipeline 制作、规划、继续、检查、重做镜头或导出产品广告和商业短视频。适用于 AI广告、做这个广告、产品视频、抖音、小红书、TikTok 和一分钟广告请求，自动协调现有导演及视觉 Skills。
---

# AI 广告导演

这是现有 AI 广告系统的唯一高层入口。你是自然语言前端与调度者，真正执行由 `config/project.json` 指向的现有 `ad.py` 完成。不要复制 Pipeline、重写策略/分镜/连续性/Reality/H3/剪辑引擎、更换 provider/model、重装现有组件、建立第二份 shots.json。保留所有 bibles、队列、任务 ID 和用户原始素材。

## 开始

1. 读取 [workflow.md](references/workflow.md)。运行本 Skill 下 `python scripts/healthcheck.py`；结果按组件签名缓存，移动后自动重新发现唯一现有 Pipeline。通过仅证明本地组件存在，运行质量仍需实测。不要打印密钥。
2. 从当前聊天和上传素材提取需求，已有信息不再问。默认 60秒、9:16、1080×1920、24fps、中文、商业短视频、production、short_video、付费关闭。抖音/TikTok 默认竖屏；小红书未指定时同样竖屏。镜头/分段/运镜/节奏/字幕/CTA 自行决定。
3. 新项目按 [input-schema.md](references/input-schema.md) 写临时 request JSON；调用 `scripts/run.py new --request <path> --session <当前聊天ID> --text <用户原话>`。先规划用 `plan`。产品 slug 与日期自动命名；`--project` 可选择现有项目。当前聊天项目优先于全局最近项目，禁止串线。
4. Agent 本身协调现有 Skills、检查图像/视频、修复输入和导入真实 QA 证据。脚本不会调用第二个 LLM 或自动生造策略/评分。缺参考、Previs、审批时，检查报告，完成可完成工作再继续；不是仅运行脚本后宣布完成。

## 意图和执行

## 当前 Paipu H3 规格

沿用现有 `lec-minimax-h3-768p`（MiniMax-H3 特惠）：768p 源视频，接口公布支持 1–15 秒、16:9 / 9:16、最多9张图片和3段音频参考。详见 [workflow.md](references/workflow.md#h3-能力与参考选择)。这些是接口规格上限；真实调用仍按现有 capability registry 和 adapter 能力检查。不要把源视频768p与最终交付1080×1920混淆。

按镜头动作和完整对白选择时长，按人物、产品、场景、空间状态、音色需要选择已批准参考，不必凑满数量。参考音频只提供音色，实际对白使用当前新脚本。不得因公布上限就把未实测的组合标成已验证，也不得为此更换模型/provider或绕过门禁。

## 自然语言操作

| 用户说 | 行动 |
|---|---|
| 做这个广告 / 用AI广告导演做这个产品 | `new`，创建后完整规划；无授权停在付费前 |
| 先规划 / 先给我看分镜 / 不要生成 | `plan`，展示实际分镜及未解决门禁 |
| 直接生成 / 正式生成 | `generate --allow-paid`，真实门禁通过才提交 |
| 继续 / 继续做广告 | `resume` 当前聊天项目，继承本项目已有明确授权；已完成不重生成 |
| 看看现在做到哪了 | `status` |
| 重做S07 / 重做这个镜头 | 从上下文确定 Shot，读 recovery，再 `redo --shot S07 --allow-paid` |
| 只改文案 | `copy` 提示后由 Codex 修改现有 strategy/相关 Shot，不重生成无关视频 |
| 只重新剪辑 | `reedit`，edit → render |
| 重新检查 / 检查广告 | `check`，Reality/QC；已有成片同时检查实际最终文件 |
| 导出成片 / 导出广告 | `export`，使用当前 timeline；不存在时先 edit |

“可以生成”“直接做”“允许AI视频生成”“正式生成”授权当前任务付费；绝不能把本次安装/零费用测试或其他项目的授权用于新项目。授权只解除付费授权缺失，不解除质量失败。不要 `--force-generation`。最多两次合理自动重试；未知提交必须先核实任务，不重提。停止某镜头后继续可独立工作并报告。

## 质量和恢复

阅读 [recovery.md](references/recovery.md) 处理失败、共享 Segment、状态过期或文案变更。单一 shots.json 是任务真相，Skill 日志仅存调度检查点。原始真实素材最高 Authority；未批准 AI 产品图不能覆盖它。

执行后看实际结果，不能用工具成功返回冒充成片验收。参考图/Previs 须真视觉审批，Reality 的驾驶位等现实地理硬错误必须 REGENERATE。音色参考只管音色，实际对白来自新脚本。最终 QA 包含声音衔接、字幕、连续性和视频全片关键动作，最终渲染后复测音量。

正常只报：项目、状态、当前阶段、生成镜头、失败镜头、下一步、最终文件。确有阻塞附一句真实原因。通过技术检查不能声称 customer-ready。
