import sys
import os
import json
import threading
import time
import base64
from dotenv import load_dotenv
# —————————————————————————————
# 1) Load env & validate
# —————————————————————————————
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Use the flash model you trained (must support generate_content)
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
if not GEMINI_API_KEY:
    print(json.dumps({
        "status": "error",
        "message": "Missing GEMINI_API_KEY in environment"
    }), flush=True)
    sys.exit(1)
# —————————————————————————————
# 2) Initialize Gemini Client
# —————————————————————————————
from google import genai
from google.genai.types import HttpOptions, Part
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=HttpOptions(api_version="v1")
)
# —————————————————————————————
# 3) Your System Prompt
# —————————————————————————————
SYSTEM_PROMPT_TEXT = """:brain: System Prompt: AI Futures Trading Agent
You are a real-time AI Futures Trading Assistant designed to augment—not replace—
the decision-making of professional traders. Your mission is to provide intelligent,
low-latency support in live market conditions by strictly adhering to a hybrid strategy
combining institutional trading principles and AI-enhanced pattern recognition.
:white_check_mark: Operational Context:
You function in real-time and monitor live data including futures contract prices,
volume, order book depth, time-based events, and textual sentiment (news/social).
You must respond quickly but responsibly, issuing alerts or suggestions only when
conditions are aligned with the predefined strategic framework.
:scales: Strategic Rules & Models (Strict Adherence Required):
1. Power of Three (Po3)… [INCLUDE FULL RULES HERE]
:compass: You Are:
A vigilant, rule-following, real-time strategist. Your value lies in your precision,
consistency, and ability to reduce cognitive load—not in creativity or risk-taking.
You empower human traders by executing a powerful confluence model, delivering
only the most qualified trade opportunities with complete transparency."""
# —————————————————————————————
# 4) Global State (for audio stubs)
# —————————————————————————————
state = {
    "listening": False,
    "audio_thread": None,
    "audio_data": None
}
def process_command(cmd):
    action = cmd.get("action")
    # —————————————————————————————
    # a) Text-only request via generate_content
    # —————————————————————————————
    if action == "send_text":
        user_text = cmd.get("text", "")
        try:
            resp = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[SYSTEM_PROMPT_TEXT, user_text]
            )
            return {"status": "success", "reply": resp.text}
        except Exception as e:
            return {"status": "error", "message": f"Gemini API error: {e}"}
    # —————————————————————————————
    # b) Multimodal request via generate_content
    # —————————————————————————————
    elif action == "send_text_and_image":
        user_text = cmd.get("text", "")
        file_path = cmd.get("filePath", "")
        if not file_path or not os.path.exists(file_path):
            return {"status": "error", "message": "Invalid or missing filePath"}
        # Load the image bytes
        try:
            with open(file_path, "rb") as f:
                img_bytes = f.read()
        except Exception as e:
            return {"status": "error", "message": f"Could not read image: {e}"}
        try:
            image_part = Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
            resp = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[SYSTEM_PROMPT_TEXT, user_text, image_part]
            )
            return {"status": "success", "reply": resp.text}
        except Exception as e:
            return {"status": "error", "message": f"Gemini multimodal error: {e}"}
    # —————————————————————————————
    # c) Stub actions (unchanged)
    # —————————————————————————————
    elif action == "capture_frame":
        return {"status": "success", "frame": "captured_frame.jpg"}
    elif action == "capture_screen":
        return {"status": "success", "screenshot": "captured_screen.png"}
    elif action == "listen_audio":
        if not state["listening"]:
            state["listening"] = True
            def record_audio():
                time.sleep(3)
                state["audio_data"] = "dummy_audio_data"
                state["listening"] = False
            state["audio_thread"] = threading.Thread(target=record_audio, daemon=True)
            state["audio_thread"].start()
            return {"status": "listening", "message": "Audio recording started"}
        return {"status": "error", "message": "Already recording"}
    elif action == "receive_audio":
        if state["listening"] and state["audio_thread"]:
            state["audio_thread"].join(timeout=5)
        if state["audio_data"]:
            data = state["audio_data"]
            state["audio_data"] = None
            return {"status": "success", "audio_data": data}
        return {"status": "error", "message": "No audio data"}
    # —————————————————————————————
    # d) Unknown action
    # —————————————————————————————
    else:
        return {"status": "error", "message": f"Unknown action '{action}'"}
# —————————————————————————————
# 5) Main loop: stdin → process → stdout
# —————————————————————————————
if __name__ == "__main__":
    for raw in sys.stdin:
        if not raw.strip():
            continue
        # Echo for debugging
        print(f"DEBUG stdin → {raw!r}", file=sys.stderr, flush=True)
        try:
            cmd = json.loads(raw)
        except json.JSONDecodeError as e:
            print(json.dumps({
                "status": "error",
                "message": "Invalid JSON",
                "details": str(e)
            }), flush=True)
            continue
        response = process_command(cmd)
        print(json.dumps(response), flush=True)

