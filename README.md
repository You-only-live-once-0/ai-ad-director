# ai-ad-director

Codex Skill for directing an **existing** AI ad pipeline with natural language. It coordinates planning, continuity, reality checks, references, previsualization, paid gates, generation, QC, transcription and editing through that pipeline's `ad.py`. It does not bundle or recreate the production system.

## Use

Install this folder as `~/.codex/skills/ai-ad-director`, then say:

> 用 AI 广告导演做这个产品，60 秒，抖音竖屏。

The local pipeline must already contain `ad.py`, `director/`, `providers/current_video_provider.py` and its working dependencies. Set `config/project.json` from [project.example.json](config/project.example.json), or let `scripts/healthcheck.py` find one unambiguous `ai-ad-pipeline` under `~/Documents/Codex`. This machine-specific config stays local and is ignored by Git.

Run `python scripts/healthcheck.py` for local availability. Use `python scripts/run.py interpret --text "先规划不要生成"` to check intent routing. The user's product facts, approved assets and evidence remain necessary for a real ad. This Skill does not grant provider access or bypass preflight, reference, continuity and Reality QA.

The Paipu MiniMax-H3 768p service advertises 1–15 second sources, 16:9/9:16, up to nine images and three audio references. The current linked pipeline decides which combinations are proven and may be submitted; documentation limits alone do not mark them live verified.

## What is published

`SKILL.md`, workflow references, a local health check, the dispatcher and a portable config example. No API keys, project footage, provider credentials, machine path bindings, sessions or paid job history are included.

The dispatcher operates the existing pipeline; it is not a standalone video generator. Its existing planner currently accepts 45–70 second projects. The Skill documents how to handle shorter requests without claiming that 30 second production is already automated.
