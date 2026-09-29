# 保留状态与定向恢复

- 当前项目从聊天/project/session选取，读 shots.json、generation_segments、logs/tasks、preflight、Skill检查点。已有 completed/approved/done 及可用文件不提交新请求；pending task_id 先查询；submission_uncertain 停下审计，不重新提交。
- Skill checkpoints 在项目 logs/ai_ad_director.json，只记录阶段、签名、日志、有限重试数。不是第二个 shots.json，不存另一份任务 ID。
- generate 的非零退出、QC失败、待视觉审阅都保留原 manifest。再次“继续”只补缺阶段；有输出的 pending review 先审阅，再 transcribe/voice/audio/edit/render。无变更的 done项目直接复用成片。
- 失败 Shot先找到 generation_segment_id。仅相关 segment允许重做；一个 segment覆盖多个剪辑 Shot时，现有 CLI禁止 `--shot --regenerate`，Codex先在现有 manifest规划单镜头 override或使用既有模块处理该segment，保留其他任务ID。不能绕过这个失败或写第二个队列。
- 自动重试最多2次。包装器 redo计数保存在日志；CLI 不自动循环付费。旧legacy worker另有内部重试，调用前确认上限不超过2，不在不明旧队列上开启批量付费。网络提交不确定不计作可重试的明确失败。
- 只改文案：改 strategy和对应 Shot对白，按现有编译/连续性/参考/Reality/lint/preflight重算，只使相关 segment失效，保存原素材和task审计历史。已经完成的视频内对白变化需要定向重生成，不能只换字幕伪装。
- 字幕错误：检查WhisperX转录/词时间或caption，重做必要阶段，不重生成正确视频。Remotion错误仅edit/render。音频衔接失败只修相关trim/gain/roomtone后audio-qc/edit/render。
- Paid Gate有真实错误就修，never force。授权只解除授权缺失，不能修改paid_ready、reviews、scores为true。
