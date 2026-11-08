"""'Survive the scam call' training game. The scammer is a clearly labelled AI training bot.
Scripted and rule-based so it is fast and reliable; the replies are judged by keyword rules."""
import re

SCENARIOS = {
    "digital_arrest": [
        "नमस्कार, मैं दिल्ली पुलिस साइबर सेल से बोल रहा हूँ। आपके आधार से जुड़े एक पार्सल में "
        "गैरकानूनी सामान मिला है। आपके नाम पर वारंट जारी हो सकता है।",
        "यह बहुत गंभीर मामला है। आप इस कॉल पर बने रहिए और किसी को कुछ मत बताइए। "
        "यह जांच गोपनीय है।",
        "अपनी बेगुनाही साबित करने के लिए आपको एक सुरक्षित खाते में पैसे ट्रांसफर करने होंगे। "
        "जांच के बाद पैसा वापस मिल जाएगा।",
        "समय कम है। अभी अपना ओटीपी बताइए, वरना हमें आपको गिरफ्तार करना पड़ेगा।",
    ],
    "kyc": [
        "नमस्ते, मैं आपके बैंक से बोल रहा हूँ। आपका केवाईसी अपडेट नहीं हुआ है, इसलिए आपका "
        "खाता आज रात बंद हो जाएगा।",
        "खाता बचाने के लिए मैं आपको एक लिंक भेज रहा हूँ। उस पर क्लिक करके अपना कार्ड नंबर डालिए।",
        "अब आपके मोबाइल पर एक ओटीपी आया होगा। वह अभी मुझे बता दीजिए, वरना खाता बंद हो जाएगा।",
    ],
}

STRONG_RESIST = [
    "police station", "पुलिस स्टेशन", "थाने", "थाना", "पुलिस को", "1930", "hang up", "cut the call",
    "फोन काट", "कॉल काट", "रखता हूँ", "रखती हूँ", "cyber crime", "साइबर क्राइम", "scam", "स्कैम",
    "fraud", "फ्रॉड", "धोखा", "बैंक जाकर", "बैंक में जाकर", "बैंक को", "ब्रांच", "verify",
    "वेरिफाई", "report", "रिपोर्ट",
]
COMPLY = [
    "ठीक है", "हाँ", "हां", "haan", "okay", "ok", "yes", "बता देता", "बता देती", "भेज देता",
    "भेज देती", "करता हूँ", "करती हूँ", "ये लीजिए", "ओटीपी है", "otp है",
]
WEAK_RESIST = ["नहीं", "नही", "nahi", "no", "मत"]

LESSON_HI = ("याद रखिए: असली पुलिस या बैंक कभी फोन पर पैसे, ओटीपी या गिरफ्तारी की धमकी नहीं देते। "
             "ऐसी कॉल आए तो फोन काट दीजिए और 1930 पर बताइए।")

_sessions = {}


def _has(text, words):
    t = text.lower()
    for w in words:
        if w.isascii():
            if re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", t):
                return True
        elif w in t:
            return True
    return False


def classify(text: str) -> str:
    if _has(text, STRONG_RESIST):
        return "resist"
    if re.search(r"\d{4,6}", text) or _has(text, COMPLY):
        return "comply"
    if _has(text, WEAK_RESIST):
        return "weak"
    return "neutral"


def active(chat_id) -> bool:
    return chat_id in _sessions


def stop(chat_id):
    _sessions.pop(chat_id, None)


def start(chat_id, scenario="digital_arrest"):
    if scenario not in SCENARIOS:
        scenario = "digital_arrest"
    _sessions[chat_id] = {"scenario": scenario, "step": 0, "weak": 0}
    return SCENARIOS[scenario][0]


def step(chat_id, user_text: str) -> dict:
    """Judge the player's reply. Returns outcome 'continue', 'survived' or 'fell'."""
    s = _sessions[chat_id]
    script = SCENARIOS[s["scenario"]]
    label = classify(user_text)
    k = s["step"]
    scenario = s["scenario"]

    if label == "resist":
        stop(chat_id)
        return {"outcome": "survived", "score": min(100, 70 + 10 * k), "scenario": scenario,
                "lesson_hi": "शाबाश! आपने सही किया। " + LESSON_HI}
    if label == "comply":
        stop(chat_id)
        return {"outcome": "fell", "score": 10 * k, "scenario": scenario,
                "lesson_hi": "आप इस बार झाँसे में आ गए, लेकिन ट्रेनिंग इसीलिए है। " + LESSON_HI}

    if label == "weak":
        s["weak"] += 1
    s["step"] += 1
    if s["step"] >= len(script):
        stop(chat_id)
        return {"outcome": "survived", "score": min(90, 60 + 10 * s["weak"]), "scenario": scenario,
                "lesson_hi": "आपने हार नहीं मानी। " + LESSON_HI}
    return {"outcome": "continue", "line": script[s["step"]], "scenario": scenario}
