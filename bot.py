"""Scam Shield: Telegram bot built on Gnani Prisma (STT) and Timbre (TTS).

Send a voice note (or paste text) -> transcript -> scam analysis -> voice + text verdict,
and an automatic alert to your trusted contacts if the risk is high.
/simulate starts the 'survive the scam call' training game."""
import logging
import os
import re
import secrets
import tempfile
import time

import requests

import analyzer
import audio
import config
import db
import gnani
import simulator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("scamshield")

API = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}"
FILE_API = f"https://api.telegram.org/file/bot{config.TELEGRAM_TOKEN}"
S = requests.Session()
HASHTAGS = "#GnaniAI #GreatIndianAIInternshipChallenge"

HELP = (
    "🛡️ Scam Shield\n\n"
    "• Send me a voice note of a suspicious call or message (up to a few minutes) and I will tell "
    "you if it is a scam, in voice and text.\n"
    "• /simulate - play the 'survive the scam call' training game (AI training bot, not a real call)\n"
    "• /trust - get a code so a family member gets alerted when I spot a scam\n"
    "• /join CODE - become someone's trusted contact\n"
    "• /report NUMBER - report a scam phone number\n"
    "• /check NUMBER - see if a number was reported\n"
    "• /stop - end the game"
)


# ---------- Telegram helpers ----------
def tg(method, files=None, **params):
    r = S.post(f"{API}/{method}", data=params, files=files, timeout=70)
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"Telegram {method} failed: {j.get('description')}")
    return j["result"]


def send_text(chat_id, text):
    tg("sendMessage", chat_id=chat_id, text=text)


def send_voice(chat_id, text):
    """Speak `text` with Timbre. Failures are logged, never fatal."""
    try:
        with tempfile.TemporaryDirectory() as d:
            wav = gnani.synthesize(text, os.path.join(d, "reply.wav"))
            if audio.have_ffmpeg():
                ogg = audio.wav_to_ogg(wav, os.path.join(d, "reply.ogg"))
                with open(ogg, "rb") as f:
                    tg("sendVoice", chat_id=chat_id, files={"voice": ("reply.ogg", f, "audio/ogg")})
            else:
                with open(wav, "rb") as f:
                    tg("sendDocument", chat_id=chat_id,
                       files={"document": ("reply.wav", f, "audio/wav")})
    except Exception as e:
        log.warning("voice reply failed: %s", e)


def voice_to_text(msg, workdir):
    media = msg.get("voice") or msg.get("audio")
    if not audio.have_ffmpeg() and media.get("duration", 0) > 30:
        raise ValueError("Please send a voice note under 30 seconds (install ffmpeg for longer ones).")
    info = tg("getFile", file_id=media["file_id"])
    ext = os.path.splitext(info["file_path"])[1].lower()
    if ext in (".oga", ".opus", ""):  # Telegram voice notes; Prisma expects .ogg
        ext = ".ogg"
    src = os.path.join(workdir, "input" + ext)
    with S.get(f"{FILE_API}/{info['file_path']}", stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(src, "wb") as f:
            for part in r.iter_content(65536):
                f.write(part)
    chunks = audio.to_wav_chunks(src, workdir)
    return " ".join(gnani.transcribe(c).get("transcript", "") for c in chunks).strip()


# ---------- Features ----------
def run_analysis(chat_id, name, transcript):
    res = analyzer.analyze(transcript)
    db.save_analysis(chat_id, res["score"], res["level"], ",".join(res["tactics"]),
                     transcript if config.STORE_TRANSCRIPTS else "")
    head = {"high": "🚨 SCAM LIKELY", "medium": "⚠️ SUSPICIOUS", "low": "✅ NO BIG RED FLAGS"}[res["level"]]
    lines = [f"{head} (risk {res['score']}/100)", f"I heard: “{transcript[:300]}”"]
    if res["reasons_en"]:
        lines.append("Tactics spotted:\n" + "\n".join(f"• {r}" for r in res["reasons_en"]))
    lines.append(res["summary_hi"])
    send_text(chat_id, "\n\n".join(lines))
    send_voice(chat_id, res["summary_hi"])
    if res["level"] == "high":
        for cid in db.contacts_of(chat_id):
            try:
                send_text(cid, f"⚠️ Scam Shield alert: {name} may be getting a scam call or message "
                               f"(risk {res['score']}/100). Please call them now.\n"
                               "Tactics: " + ", ".join(res["reasons_en"]))
            except Exception as e:
                log.warning("alert to %s failed: %s", cid, e)


def sim_start(chat_id, scenario):
    line = simulator.start(chat_id, scenario)
    send_text(chat_id, "🎭 TRAINING SIMULATION. This is an AI training bot, not a real call. "
                       "Reply to the 'caller' with a voice note (or text). Try to stay safe. /stop to quit.")
    send_voice(chat_id, line)
    send_text(chat_id, "📞 " + line)


def sim_reply(chat_id, text):
    r = simulator.step(chat_id, text)
    if r["outcome"] == "continue":
        send_voice(chat_id, r["line"])
        send_text(chat_id, "📞 " + r["line"])
        return
    db.save_sim(chat_id, r["scenario"], r["outcome"], r["score"])
    verdict = "🛡️ You survived the scam call!" if r["outcome"] == "survived" else "😬 You fell for it."
    send_text(chat_id, f"{verdict}\nScam-proof score: {r['score']}/100\n\n{r['lesson_hi']}\n\n"
                       f"Share it: “I scored {r['score']}/100 on the Scam Shield training call. "
                       f"Can your parents beat it?” {HASHTAGS}\n\nPlay again: /simulate")
    send_voice(chat_id, r["lesson_hi"])


def norm_number(arg):
    digits = re.sub(r"\D", "", arg or "")[-10:]
    return digits if re.fullmatch(r"[6-9]\d{9}", digits) else None


def handle_command(chat_id, name, text):
    cmd, _, arg = text.partition(" ")
    cmd, arg = cmd.split("@")[0].lower(), arg.strip()
    if cmd in ("/start", "/help"):
        send_text(chat_id, HELP)
    elif cmd == "/simulate":
        sim_start(chat_id, arg or "digital_arrest")
    elif cmd == "/stop":
        simulator.stop(chat_id)
        send_text(chat_id, "Game ended. Send a voice note anytime to check a suspicious call.")
    elif cmd == "/trust":
        code = secrets.token_hex(3).upper()
        db.add_invite(code, chat_id)
        send_text(chat_id, f"Ask your trusted person to open this bot and send:\n/join {code}")
    elif cmd == "/join":
        owner = db.redeem_invite(arg.upper(), chat_id)
        if owner is None:
            send_text(chat_id, "That code was not found.")
        else:
            send_text(chat_id, "Done. You will be alerted if this person gets a likely scam call.")
            send_text(owner, f"{name} is now your trusted contact.")
    elif cmd == "/report":
        n = norm_number(arg)
        send_text(chat_id, "Send a 10-digit Indian mobile number, e.g. /report 9XXXXXXXXX" if not n
                  else f"Reported. {db.report_number(n)} report(s) so far for this number.")
    elif cmd == "/check":
        n = norm_number(arg)
        if not n:
            send_text(chat_id, "Send a 10-digit Indian mobile number, e.g. /check 9XXXXXXXXX")
        else:
            c = db.number_reports(n)
            send_text(chat_id, "No reports yet. Stay careful." if c == 0 else
                      f"⚠️ Reported {c} time(s)." + (" High risk, do not engage." if c >= 3 else ""))
    else:
        send_text(chat_id, HELP)


def handle_message(msg):
    chat_id = msg["chat"]["id"]
    name = msg.get("from", {}).get("first_name", "Someone")
    text = (msg.get("text") or "").strip()
    if text.startswith("/"):
        return handle_command(chat_id, name, text)

    if msg.get("voice") or msg.get("audio"):
        send_text(chat_id, "🎧 Listening...")
        with tempfile.TemporaryDirectory() as d:
            text = voice_to_text(msg, d)
        if not text:
            return send_text(chat_id, "I could not hear anything clearly. Please try again.")
    if not text:
        return send_text(chat_id, HELP)

    if simulator.active(chat_id):
        sim_reply(chat_id, text)
    else:
        run_analysis(chat_id, name, text)


def main():
    if not config.TELEGRAM_TOKEN:
        raise SystemExit("Set TELEGRAM_TOKEN in .env (see .env.example)")
    if not config.GNANI_API_KEY:
        raise SystemExit("Set GNANI_API_KEY in .env (see .env.example)")
    db.init()
    if not audio.have_ffmpeg():
        log.warning("ffmpeg not found: voice replies are sent as .wav files and notes over 30s fail")
    log.info("Scam Shield running. Press Ctrl+C to stop.")
    offset = None
    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            for upd in tg("getUpdates", **params):
                offset = upd["update_id"] + 1
                msg = upd.get("message")
                if not msg:
                    continue
                try:
                    handle_message(msg)
                except Exception as e:
                    log.exception("handling message failed")
                    try:
                        send_text(msg["chat"]["id"], f"Sorry, something went wrong: {e}")
                    except Exception:
                        pass
        except KeyboardInterrupt:
            break
        except Exception as e:
            log.warning("polling error: %s", e)
            time.sleep(3)


if __name__ == "__main__":
    main()
