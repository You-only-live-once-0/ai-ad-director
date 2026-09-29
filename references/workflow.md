# 现有流程与能力调度

读取链接项目的 AGENTS.md 和当前 config/h3_capability_registry.json。历史说明可能早于真实探针；能力以当前 registry、真实日志及现有 adapter 可发送字段为准。不要因为 schema 接受就宣称音色相似度通过。

## Codex 的工作

## H3 能力与参考选择

当前用户确认的 Paipu **MiniMax-H3 特惠768p** 接口规格：单次源视频 **1–15秒**，**16:9 / 9:16**，图片参考最多 **9张**，音频参考最多 **3段**。规格以当前服务目录为准；不将上游旧版4–15秒限制误当成这个接口的完整范围。官方目录地址：`https://api.paipu.net/api/media-models/catalog?surface=docs`。本次更新依据用户提供的规格和项目已有目录证据，未做新付费探针。

| 能力层级 | 当前说明 |
|---|---|
| 公布的接口范围 | 1–15秒、两种画幅、最多9图/3音频 |
| 项目已有真实成功记录 | 请求4秒、6秒；6秒探针使用1图+1音频、原生声音 |
| 现有生产门禁记录 | 时长 verified_values=[4,6]；图片/音频当前验证上限各1 |
| 仍需验证 | 其他时长、多图/多音频组合及音色相似度；尾帧语义不由多图数量自动推断 |

规划可考虑完整公布范围，但付费提交前必须确认现有 adapter 能序列化所需字段、参考已批准、对应能力证据满足门禁。不直接修改 registry 把1–15所有值和9图/3音频全标为 live_verified。缺能力验证且本项目已授权测试时，使用最小必要探针和合理费用范围验证成功后更新证据；本次 Skill 微调不触发视频生成。

多图按人物/产品/场景/前序状态的确切角色组织，只送需要的已批准图片；多音频绑定到对应人物，避免混淆声线。不能把图像格子当成多张独立参考。新对白始终来自脚本，参考音频原句不自动复用。源768p按现有Remotion导出目标分辨率，不宣称模型原生1080p。

## 生产调度

使用已安装 SuperCMO 的 analyzing-products、writing-ad-copy 等能力处理真实产品资料与 strategy，不凭空造功效、价格或参数。读取 video-talkcraft、video-shotcraft、story-video-director、visual-image/visual-video、h3-prompt-writing、video-storyboard 作导演/视觉/提示词指导。Spatial Continuity Engine、WORLD_BIBLE、character/product/location/voice/camera/lighting bibles 和 Audio World 全部沿用项目模块。需要 3D 时由现有灰盒模块处理，不另写引擎。

`run.py` 的顺序：plan（已有 shots.json 则跳过）→ continuity → reality → refs → previs → qc-previs → reality-qc → voice-check → h3-lint → preflight → 条件触发 previs3d 后再 preflight。规划/未授权在此停止。进入付费前读完整 preflight，必须 paid_ready=true。

CLI 的 refs/previs 只整理参考和提示词，不能代替生成真实模型图片和视觉验收。Codex 用现有图片工具生成缺失候选，保留真实用户素材，按现有 reference/reality 协议审阅、登记 media/context SHA 和证据，核对 contact sheet 后重跑检查。当前 `qc-previs` 可能返回退出码0但 passed=false；必须看报告，不能忽略。国家无法确定且影响内容才问，不用图片风格猜国家。

之后 generate --allow-paid → reality-qc → qc → 真实视觉审阅/连续性证据 → transcribe（WhisperX）→ voice-qc → audio-qc → edit（Remotion）→ render → 最终文件视觉/声音/字幕/连续性验收。脚本发现待审即停在正确阶段；Codex 完成审阅再继续，禁止伪造通过。未完成声音身份、speech complete 等条件由现有编辑门禁继续阻断。

脚本缓存完成阶段的输入签名；改变素材、bibles、reviews、策略或规划会重新检查。现有任务状态/ID不被缓存覆盖。成片存在时先核对状态与输入是否变化；无变化直接交付原成片，不重新渲染。渲染使用共享 Remotion timeline，多个项目按顺序 edit→render，禁止并发互相覆盖。

## 当前真实边界

现有 plan 自动种子仅支持45–70秒；30秒请求必须保留请求本身，先用现有规划器产生可编辑种子，由 Codex 在同一 shots.json 精简镜头和对白、调整时长，并调用现有 validate/continuity/h3 build/compile 检查，不能静默改成60秒。若现有验证仍拒绝，报告具体限制，不声称30秒自动成片已经验证。不要为包装任务修改生产引擎。

共享 segment 的单 shot 重做目前被现有 CLI 拒绝。按 recovery 规划该相关 segment或单镜头 override 后继续，不因这一点重做整条广告。Video Vision 的文件存在不证明 MCP 已可运行；优先当前 callable 视频工具，失败则用本地 ffmpeg 抽帧+Codex视觉与实际听音完成审核，不冒充自动评分。
