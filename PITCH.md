# Scam Shield: a voice-first scam-call shield for Indian families

*Built by Pabolu Amrutha Sai Spandana for the Great Indian AI Internship Challenge, using Gnani Prisma and Gnani Timbre.*

## The problem
Fake "police", KYC and courier calls pressure people into sending money or sharing OTPs. Parents and grandparents are the easiest targets: they are often alone when the call comes, there is no one to ask in the moment, and many are more comfortable in Hindi than in reading English text.

## The solution
**Scam Shield** is a Telegram bot. Send it a suspicious voice note (or paste the message) and within seconds it replies with a scam verdict, the tactics it spotted, and a **spoken warning in Hindi**.

## How it works
1. **Gnani Prisma (speech to text)** transcribes the voice note, with automatic Indian-language detection.
2. **Scam Shield's analyzer** scores the risk from 0 to 100 and lists the tactics: fake authority, arrest threats, urgency, secrecy, payment demands, OTP/KYC requests and prize bait. It uses a Hindi and English rule engine, with an optional plug-in for an LLM such as Gnani Evon.
3. **Gnani Timbre (text to speech)** speaks the verdict in Hindi, so the person hears the warning instead of having to read it.
4. On a high-risk result, **trusted family contacts are alerted automatically**.

## Also built in
- **"Survive the scam call" game** (`/simulate`): a clearly labelled AI "scammer" to practise saying no, with a score at the end.
- **Community scam-number list** (`/report`, `/check`).
- **Privacy by default:** transcripts are not stored unless the host turns it on.

## Why it matters
- **Voice-first:** no typing or reading needed, and the answer comes back in the user's language.
- **Low cost and low barrier:** the speech models are hosted by Gnani, so the bot runs on an ordinary 8 GB laptop with no GPU.
- **Prevention, not cure:** the check takes seconds, before any money moves.

## Demo
The demo video shows a scripted, AI-generated scam voice note being transcribed, scored 85/100 (fake police, arrest threat, OTP demand) and answered with a Hindi voice warning.

## Limitations and next steps
- Scoring is rule-based, so it is a guide, not proof: if in doubt, hang up and call the bank or the cyber-crime helpline 1930.
- Very quiet or noisy recordings can be mistranscribed.
- Next: deeper analysis with an LLM such as Gnani Evon, more regional languages, and shared scam-number alerts.

Code and setup: see `README.md`.
