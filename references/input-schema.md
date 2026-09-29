# 输入：由 Codex 从聊天填充

无需用户填表。创建 request JSON，含 `product_slug`、`strategy` 和可选 `assets`。它是前端输入，不存 shots/jobs。strategy 按现有项目 schema 提供 product、approved_claims、audience、pain_point、angle、hook、script（句子数组）、cta、style、character_bible、product_bible、style_bible、reference_images、duration，以及已有 world/spatial/voice 等输入。新项目只用真实已知信息。无事实就不写价格/功效；确实没有产品信息时一次询问关键资料。

assets 每项是 `{ "path": "绝对原文件路径", "role": "product", "authority": "user_original" }`。
role 支持 product、character、location、voice、reference_ad、logo、brand、product_info，保存到现有项目 references/<role>/；logs/skill_assets.json 仅记录来源，不是另一份任务队列。原文件不移动。复制后 Codex 将正确相对路径绑定到 strategy.reference_images / product、character、voice bible 和现有 reference registry；引用前仍需 QA。同名冲突报错后选择明确的新文件名，绝不覆盖。

session 使用真实当前聊天 ID。脚本允许 `--project` 明确覆盖；继续优先当前上下文项目，不凭哪个文件最近来猜。默认 paid=false；可保存项目已授权范围但不能跨项目继承。request中的授权布尔值不单独授权 API；由用户原话/--allow-paid决定。

示例调度（路径相对本 Skill，生产 cwd 自动设定）：
```
python scripts/run.py plan --request <request.json> --session <chat-id> --text "用AI广告导演做一个60秒保温杯抖音广告，先规划不要生成。"
python scripts/run.py status --session <chat-id>
python scripts/run.py resume --session <chat-id> --allow-paid
```
