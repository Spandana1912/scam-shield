"""Scam analysis. A rule engine works offline with no extra setup.
If LLM_BASE_URL and LLM_MODEL are set (any OpenAI-compatible endpoint, such as a hosted
Evon), the LLM is asked too and the higher risk score wins, since a missed scam costs more
than a false alarm."""
import json
import re

import requests

import config

# tactic -> (weight, English label, Hindi reason)
TACTICS = {
    "authority": (20, "Claims to be police / government / bank",
                  "खुद को पुलिस या सरकारी अधिकारी बताना"),
    "threat": (20, "Threatens arrest or account closure",
               "गिरफ्तारी या कार्रवाई की धमकी देना"),
    "urgency": (15, "Creates urgency", "जल्दबाज़ी का दबाव बनाना"),
    "isolation": (25, "Tells you to keep it secret / stay on the line",
                  "किसी को न बताने या कॉल पर बने रहने को कहना"),
    "payment": (25, "Asks for money transfer", "पैसे ट्रांसफर करने को कहना"),
    "credentials": (30, "Asks for OTP / PIN / Aadhaar / KYC / app install",
                    "ओटीपी, पिन या निजी जानकारी माँगना"),
    "prize": (15, "Lottery / prize bait", "इनाम या लॉटरी का लालच देना"),
}

KEYWORDS = {
    "authority": ["police", "cbi", "enforcement directorate", "customs", "narcotics", "trai",
                  "cyber cell", "court", "officer", "inspector", "पुलिस", "सीबीआई", "कस्टम",
                  "नारकोटिक्स", "ट्राई", "साइबर सेल", "कोर्ट", "अदालत", "अधिकारी", "इंस्पेक्टर"],
    "threat": ["arrest", "warrant", "jail", "blocked", "suspend", "legal action", "fir",
               "गिरफ्तार", "वारंट", "जेल", "ब्लॉक", "बंद हो जाएगा", "कानूनी कार्रवाई",
               "एफआईआर", "केस दर्ज"],
    "urgency": ["immediately", "urgent", "right now", "last chance", "today only", "अभी",
                "तुरंत", "तुरन्त", "जल्दी", "फौरन", "आज ही", "वरना", "समय कम"],
    "isolation": ["don't tell", "do not tell", "stay on the line", "do not disconnect",
                  "confidential", "किसी को मत बताना", "किसी को न बताएं", "किसी को नहीं बताना",
                  "कॉल मत काटना", "फोन मत काटना", "कॉल पर बने रहिए", "गोपनीय"],
    "payment": ["transfer", "payment", "upi", "gift card", "safe account", "deposit", "rupees",
                "ट्रांसफर", "भुगतान", "पेमेंट", "यूपीआई", "गिफ्ट कार्ड", "सुरक्षित खाते",
                "जुर्माना", "जमा करें", "रुपये", "रुपए"],
    "credentials": ["otp", "pin", "cvv", "password", "aadhaar", "aadhar", "kyc", "anydesk",
                    "teamviewer", "card number", "apk", "ओटीपी", "पिन", "सीवीवी", "पासवर्ड",
                    "आधार", "केवाईसी", "कार्ड नंबर", "एनीडेस्क", "टीमव्यूअर", "लिंक पर क्लिक"],
    "prize": ["lottery", "prize", "cashback", "winner", "लॉटरी", "इनाम", "कैशबैक", "विजेता"],
}

SUMMARY_HI = {
    "high": "यह एक स्कैम कॉल लग रही है। कृपया फोन काट दीजिए। किसी को पैसे या ओटीपी मत दीजिए। "
            "साइबर क्राइम हेल्पलाइन 1930 पर बताइए।",
    "medium": "यह कॉल संदिग्ध लगती है। पैसे या कोई जानकारी देने से पहले अपने परिवार से बात कीजिए "
              "और बैंक के आधिकारिक नंबर पर खुद फोन करके पूछिए।",
    "low": "इसमें स्कैम के बड़े संकेत नहीं मिले, फिर भी सावधान रहिए और ओटीपी किसी को मत बताइए।",
}


def _match(text: str, kw: str) -> bool:
    if kw.isascii():
        tail = r"(?![a-z0-9])" if len(kw) <= 4 else ""
        return re.search(r"(?<![a-z0-9])" + re.escape(kw) + tail, text) is not None
    return kw in text


def rule_analyze(transcript: str) -> dict:
    text = transcript.lower()
    found = [t for t, kws in KEYWORDS.items() if any(_match(text, k) for k in kws)]
    score = min(100, sum(TACTICS[t][0] for t in found))
    return {"score": score, "tactics": found}


def _level(score: int) -> str:
    return "high" if score >= 60 else "medium" if score >= 30 else "low"


def _llm_analyze(transcript: str):
    if not (config.LLM_BASE_URL and config.LLM_MODEL):
        return None
    system = (
        "You analyse transcripts of phone calls or messages for Indian scam patterns "
        "(digital arrest, fake KYC, courier or customs scams, lottery, tech support). "
        "Reply with ONLY JSON: {\"score\": 0-100, \"tactics\": [subset of "
        + json.dumps(list(TACTICS)) + "], \"summary\": \"two short sentences in Hindi "
        "(Devanagari) telling the listener what to do\"}."
    )
    try:
        r = requests.post(
            f"{config.LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
            json={"model": config.LLM_MODEL, "temperature": 0.2, "max_tokens": 600,
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": transcript}]},
            timeout=60,
        )
        content = r.json()["choices"][0]["message"]["content"]
        j = json.loads(re.search(r"\{.*\}", content, re.S).group(0))
        return {"score": int(j.get("score", 0)),
                "tactics": [t for t in j.get("tactics", []) if t in TACTICS],
                "summary": str(j.get("summary", "")).strip()}
    except Exception:
        return None


def analyze(transcript: str) -> dict:
    res = rule_analyze(transcript)
    llm = _llm_analyze(transcript)
    summary = None
    if llm:
        res["score"] = max(res["score"], max(0, min(100, llm["score"])))
        res["tactics"] = sorted(set(res["tactics"]) | set(llm["tactics"]))
        summary = llm["summary"] or None
    res["level"] = _level(res["score"])
    res["summary_hi"] = (summary or SUMMARY_HI[res["level"]])[:350]
    res["reasons_en"] = [TACTICS[t][1] for t in res["tactics"]]
    res["reasons_hi"] = [TACTICS[t][2] for t in res["tactics"]]
    res["used_llm"] = llm is not None
    return res
