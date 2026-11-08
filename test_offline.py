"""Offline checks for the analyzer and simulator. Run: python test_offline.py"""
import os
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")

import analyzer  # noqa: E402
import db  # noqa: E402
import simulator  # noqa: E402

SCAM_HI = ("मैं दिल्ली पुलिस साइबर सेल से बोल रहा हूँ। आपके आधार से जुड़े पार्सल में गैरकानूनी सामान "
           "मिला है। आपको गिरफ्तार किया जा सकता है। किसी को मत बताना और अभी सुरक्षित खाते में "
           "ट्रांसफर करें और ओटीपी बताइए।")
SCAM_EN = ("This is CBI. Your Aadhaar is linked to an illegal parcel. Transfer money immediately to a "
           "safe account or you will be arrested.")
BENIGN = "हेलो, कल शाम को घर आ जाना, खाना साथ में खाएंगे।"
BENIGN_EN = "Hi, I'm fine, are you coming for dinner tomorrow? Bring your spinning bike."

checks = []


def check(name, cond):
    checks.append(cond)
    print(("PASS" if cond else "FAIL"), name)


r = analyzer.analyze(SCAM_HI)
check("Hindi scam is high", r["level"] == "high" and r["score"] >= 90)
r = analyzer.analyze(SCAM_EN)
check("English scam is high", r["level"] == "high")
r = analyzer.analyze(BENIGN)
check("Hindi benign is low", r["level"] == "low" and r["score"] == 0)
r = analyzer.analyze(BENIGN_EN)
check("English benign is low (no 'pin' in 'spinning')", r["level"] == "low")
check("standalone 'PIN' request is flagged",
      "credentials" in analyzer.analyze("Please tell me your ATM PIN")["tactics"])

# simulator
simulator.start(1)
check("strong resist wins", simulator.step(1, "मैं पुलिस स्टेशन जा रहा हूँ")["outcome"] == "survived")
simulator.start(2)
check("OTP digits lose", simulator.step(2, "मेरा ओटीपी 482913 है")["outcome"] == "fell")
simulator.start(3)
r = simulator.step(3, "आप कौन बोल रहे हैं")
check("neutral continues", r["outcome"] == "continue" and "line" in r)
simulator.start(4, "kyc")
outs = [simulator.step(4, "क्या मतलब")["outcome"] for _ in range(3)]
check("neutral all the way survives", outs == ["continue", "continue", "survived"])

# db
db.init()
check("report counter", db.report_number("9876543210") == 1 and db.report_number("9876543210") == 2)
db.add_invite("ABC123", 10)
check("invite flow", db.redeem_invite("ABC123", 20) == 10 and db.contacts_of(10) == [20])

print(f"\n{sum(checks)}/{len(checks)} passed")
sys.exit(0 if all(checks) else 1)
