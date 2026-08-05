# Video DEMO Script — Parallel Universe Simulator

**Duration**: 3.5 minutes  
**Language**: English narration + Chinese subtitles  
**Format**: Screen recording + voiceover  
**Resolution**: 1920x1080, 30fps  

---

## Scene 1 — Opening (0:00-0:25)

| Time | English Narration | Chinese Subtitle | Screen |
|---|---|---|---|
| 0:00 | "Hi, I'm west from Team SilentCore. This is our entry for AMD Track 2: Private AI Agent Development." | 你好，我是 SilentCore 团队的 west。这是我们参加 AMD Track 2 的作品：私有 AI Agent 开发。 | Black screen → Team logo "SilentCore" fade in |
| 0:08 | "Most AI assistants are generic. They don't know YOU. They can't tell you what YOU would do in a different situation." | 大多数 AI 助手都是通用的。它们不了解你，无法告诉你：在不同情境下，你会做出什么选择。 | Fade to code editor showing generic chatbot |
| 0:17 | "We built something different. A Parallel Universe Simulator that learns your personality from your own notes, and simulates alternative life paths — entirely on your local GPU." | 我们做了一个不同的东西：平行宇宙模拟器。它从你的笔记中学习你的人格，模拟不同的人生路径——全部在你的本地 GPU 上运行。 | Screen split: left = diary text, right = GPU info |

---

## Scene 2 — The Privacy Problem (0:25-0:45)

| Time | English Narration | Chinese Subtitle | Screen |
|---|---|---|---|
| 0:25 | "Here's the problem. Your diary contains your deepest regrets, fears, and dreams." | 问题是：你的日记里藏着最深的后悔、恐惧和梦想。 | Show real diary excerpt (anonymized) |
| 0:32 | "Uploading this to ChatGPT or Claude means trusting a cloud provider with your soul. That's not acceptable." | 把它们上传到 ChatGPT 或 Claude，意味着把灵魂交给云服务商。这不可接受。 | Show cloud upload animation with red X |
| 0:40 | "Our solution: Run a 14-billion-parameter model locally on AMD ROCm. Zero data leaves your machine." | 我们的方案：在 AMD ROCm 上本地运行 140 亿参数的大模型。数据零外流。 | Show AMD W7900 card, "Local Only" badge |

---

## Scene 3 — Architecture (0:45-1:15)

| Time | English Narration | Chinese Subtitle | Screen |
|---|---|---|---|
| 0:45 | "Here's how it works. Three layers." | 工作原理分三层。 | Clean architecture diagram |
| 0:50 | "Layer one: Personality Engine. It reads your notes and extracts psychological dimensions — risk tolerance, social preference, career drive." | 第一层：人格引擎。读取笔记，提取心理维度：风险偏好、社交倾向、事业驱动力。 | Show JSON profile extraction animation |
| 1:00 | "Layer two: RAG Memory. ChromaDB stores your life events as vectors. When simulating, we retrieve the most relevant memories for context." | 第二层：RAG 记忆。ChromaDB 将人生事件存为向量。模拟时，检索最相关的记忆作为上下文。 | Show vector search visualization |
| 1:10 | "Layer three: Parallel Universe Simulator. Qwen 14B generates alternative timelines shaped by your actual traits." | 第三层：平行宇宙模拟器。Qwen 14B 根据你的真实特质，生成替代时间线。 | Show branching timeline animation |

---

## Scene 4 — Live Demo (1:15-2:30)

| Time | English Narration | Chinese Subtitle | Screen |
|---|---|---|---|
| 1:15 | "Let me show you. First, I feed the system some personal notes." | 演示开始。首先，我输入一些个人笔记。 | Terminal: `curl /learn` with sample notes |
| 1:25 | "The engine extracts my personality profile. Risk tolerance: 0.3 — I'm cautious. Career drive: 0.8 — I'm ambitious. Decision style: analytical." | 引擎提取人格画像。风险偏好 0.3——偏谨慎。事业驱动力 0.8——有野心。决策风格：分析型。 | Show JSON profile response |
| 1:40 | "Now I ask: 'What if I had taken that startup offer in 2022?'" | 现在提问：如果 2022 年我接受了那家创业公司的 offer 会怎样？ | Terminal: `curl /simulate` with decision text |
| 1:55 | "The system generates three universes. Universe A: I took the offer. Burnout in year one, recovered by year three, now a VP. Satisfaction: 7 out of 10." | 系统生成三个宇宙。宇宙 A：我接了 offer。第一年 burnout，第三年恢复，现在是 VP。满意度：7/10。 | Show Universe A output |
| 2:10 | "Universe B: I declined. Stayed at Big Corp. Stable but regretful. Satisfaction: 5." | 宇宙 B：我拒绝了。留在大公司。稳定但后悔。满意度：5。 | Show Universe B output |
| 2:20 | "Universe C: I negotiated remote work. Best of both worlds. Satisfaction: 9." | 宇宙 C：我协商了远程工作。两全其美。满意度：9。 | Show Universe C output |

---

## Scene 5 — Idea Stress Test (2:30-3:00)

| Time | English Narration | Chinese Subtitle | Screen |
|---|---|---|---|
| 2:30 | "But this agent isn't just for life decisions. It also stress-tests your ideas." | 这个 Agent 不仅用于人生决策，还能压力测试你的想法。 | Switch to `/stress-test` endpoint |
| 2:38 | "I say: 'I want to build a local AI coaching platform.'" | 我说：我想做一个本地 AI 辅导平台。 | Terminal input |
| 2:42 | "Four roles attack simultaneously. VC says: 'Market is crowded. Why you?' Customer says: 'I'm already using Notion AI.' Competitor says: 'We'll copy this in a sprint.' Regulator says: 'Where is the mental health data stored?'" | 四个角色同时攻击。VC：市场拥挤，凭什么选你？客户：我已经在用 Notion AI 了。竞品：我们一个 sprint 就能抄完。监管：心理健康数据存在哪？ | Show four-role panel output |
| 2:55 | "Survival score: 42. Brutal, honest, and exactly what I need to hear before building." | 生存评分：42。残酷、诚实、正是我在动手前需要听到的。 | Show final score and verdict |

---

## Scene 6 — Technical Deep Dive (3:00-3:20)

| Time | English Narration | Chinese Subtitle | Screen |
|---|---|---|---|
| 3:00 | "Technically, this runs on AMD Radeon Pro W7900 with ROCm 7.2.1." | 技术上，这运行在 AMD Radeon Pro W7900 和 ROCm 7.2.1 上。 | `rocm-smi` output, GPU info |
| 3:07 | "Qwen2.5-14B-Instruct served via vLLM at 8000 tokens per second." | Qwen2.5-14B-Instruct 通过 vLLM 服务，推理速度 8000 token/秒。 | vLLM benchmark numbers |
| 3:15 | "All data stays in `/workspace/persistent/` — survives server restarts. ChromaDB is fully local." | 所有数据保存在 `/workspace/persistent/`——服务器重启不丢失。ChromaDB 完全本地。 | Directory tree, privacy badge |

---

## Scene 7 — Closing (3:20-3:30)

| Time | English Narration | Chinese Subtitle | Screen |
|---|---|---|---|
| 3:20 | "This is SilentCore. Private. Personal. Parallel." | 这就是 SilentCore。私密、个人化、平行宇宙。 | Logo animation |
| 3:25 | "Thank you, AMD. Thank you for watching." | 感谢 AMD，感谢观看。 | GitHub repo QR code |

---

## Recording Tips

1. **Terminal**: Use Windows Terminal with Cascadia Code font, dark theme, font size 14
2. **Browser**: Dark mode, zoom 110%, clean address bar
3. **Voiceover**: Speak clearly, pace ~130 words/minute, leave 1-2s silence between scenes
4. **Subtitles**: Use CapCut or剪映 to auto-generate Chinese subtitles from English audio
5. **Music**: Optional ambient background (low volume), no lyrics
6. **Total file**: Target < 500MB MP4, 1080p30

## Demo Data (Pre-loaded for Video)

Use these exact notes in the `/learn` call so output is predictable:

```json
{
  "user_id": "west",
  "notes": [
    "I always choose stability over risk, even when I know the risky path might be better",
    "My friends say I overthink everything. They're not wrong.",
    "I regret not taking that startup offer in 2022. They just got acquired for 200 million.",
    "I value freedom more than money, but I keep choosing money anyway",
    "I'm good at seeing all sides of a problem, which makes me a great advisor but a terrible decision-maker"
  ]
}
```

Expected `/simulate` decision: `"Should I have taken the startup offer in 2022?"`

This produces vivid, personality-driven universes that demonstrate the product's unique value.
