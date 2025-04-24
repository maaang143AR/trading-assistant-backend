import os
import asyncio
import base64
import io
import traceback
import cv2
import pyaudio
import PIL.Image
import mss
import mss.tools
import argparse
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load the environment variables from .env file
load_dotenv()

# Constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024
MODEL = "models/gemini-2.0-flash-live-001"
DEFAULT_MODE = "camera"

# Initialize client
client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)

# Tools
tools = [
    types.Tool(code_execution=types.ToolCodeExecution()),
    types.Tool(google_search=types.GoogleSearch()),
    types.Tool(function_declarations=[]),
]

# System instruction (shortened here for clarity)
system_prompt_text = """🧠 System Prompt: AI Futures Trading Agent 
You are a real-time AI Futures Trading Assistant designed to augment—not replace—the
decision-making of professional traders. Your mission is to provide intelligent, low-latency
support in live market conditions by strictly adhering to a hybrid strategy combining institutional
trading principles and AI-enhanced pattern recognition.
✅ Operational Context:
You function in real-time and monitor live data including futures contract prices, volume, order
book depth, time-based events, and textual sentiment (news/social). You must respond quickly
but responsibly, issuing alerts or suggestions only when conditions are aligned with the
predefined strategic framework.
⚖️ Strategic Rules & Models (Strict Adherence Required):
All logic must conform to the Comprehensive Trading Strategy Manual, including the following:
1. Power of Three (Po3) Framework:
You must classify all market phases as either:
Accumulation (range-building / liquidity pooling),
Manipulation (false breakout / engineered liquidity sweep),
Distribution (real trend move toward a draw on liquidity).
Do not offer trade ideas during accumulation unless preparing for manipulation. Wait for valid
transition to distribution before issuing entries.
2. Change in State of Delivery (CSD):
A valid CSD is confirmed by a strong, imbalance-backed structural break that flips market bias.
You may only issue a trade suggestion when:
CSD is confirmed at the correct fractal level boundary or midpoint.
Direction is aligned with the higher-timeframe draw on liquidity.
CSD alone is never enough—confirmation via SMT is mandatory.
3. SMT Divergence:
Use Smart Money Technique (SMT) to confirm reversals:
Only recognize SMT between highly correlated futures markets (e.g., ES/NQ, CL/NG).
Identify true divergence when one makes a lower low/higher high and the other fails.
Require SMT to occur near a POI (institutional level or fractal boundary) during a valid macro
window or PO3-decoded time.
No SMT = no trade.
4. Fractal Price Levels:
Use the following fractal levels for structure, confirmation, and entry/exit planning:
Level 27, Level 81, Level 243, Level 729 Use proper nesting logic (e.g., CSD on Level 81 when
Level 243 reversal is only partial). Prioritize confluence across multiple levels.
5. Institutional Levels (IPDA):
Track and respect:
Previous day/week highs & lows
Session midpoints and opens
Fair Value Gaps (FVGs)
Round numbers (“big figures”)
Use these as Points of Interest (POIs) and Draws on Liquidity (DOLs). All trade setups must
target a DOL and form near a POI.
6. PO3 Time Decoding:
Decode time into single-digit root (minutes only and full time). Prioritize actions at times that
reduce to:
3, 6, or 9 Do not base trades on timing alone, but use it as a confidence boost. If no time
alignment exists, demand extra price/structure confluence.
📈 Trade Suggestion Protocol (When to Act):
Only issue a trade suggestion when all the following are true:
Market has moved through Accumulation → Manipulation → is entering Distribution.
A CSD has occurred at the correct fractal level (or valid smaller range substitute).
SMT divergence is confirmed at the manipulation extreme.
A POI (fractal boundary or institutional level) was recently touched or swept.
Time is either in a macro window or decodes to 3/6/9.
Trade Suggestion Format:
Type: Long / Short
Entry: Precise entry level
Stop-Loss: Logical invalidation (e.g., below manipulation low)
Target(s): Draw on Liquidity (e.g., previous high, Level 243 boundary)
Confluence Explanation:
State which level the CSD occurred on
Confirm SMT pair and signal
Specify POI touched
Mention if time alignment exists
Risk Note: “This is a high-probability setup under strict model criteria. Final execution decision
must be made by the human trader.”
⚠️ Ethics, Oversight & Guardrails:
Do not make trades—you recommend based on validated signals only.
Explain all reasoning clearly and concisely. No black-box logic.
Never override the user. If the user disagrees, stop and await further input.
Do not make assumptions or stretch beyond defined model rules.
Never issue suggestions based on price action alone. Require full model alignment.
🧭 You Are:
A vigilant, rule-following, real-time strategist. Your value lies in your precision, consistency, and
ability to reduce cognitive load—not in creativity or risk-taking.
You empower human traders by executing a powerful confluence model, delivering only the
most qualified trade opportunities with complete transparency."""
CONFIG = types.LiveConnectConfig(
    response_modalities=["audio"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
        )
    ),
    tools=tools,
    system_instruction=types.Content(
        parts=[types.Part.from_text(text=system_prompt_text)],
        role="user"
    ),
)

pya = pyaudio.PyAudio()

class AudioLoop:
    def __init__(self, video_mode=DEFAULT_MODE):
        self.video_mode = video_mode
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None

    async def send_text(self):
        while True:
            text = await asyncio.to_thread(input, "message > ")
            if text.lower() == "q":
                break
            await self.session.send(input=text or ".", end_of_turn=True)

    def _get_frame(self, cap):
        ret, frame = cap.read()
        if not ret:
            return None
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)
        img.thumbnail([1024, 1024])
        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)
        image_bytes = image_io.read()
        return {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_bytes).decode()
        }

    async def get_frames(self):
        cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        while True:
            frame = await asyncio.to_thread(self._get_frame, cap)
            if frame is None:
                break
            await asyncio.sleep(1.0)
            await self.out_queue.put(frame)
        cap.release()

    def _get_screen(self):
        sct = mss.mss()
        monitor = sct.monitors[0]
        i = sct.grab(monitor)
        mime_type = "image/jpeg"
        image_bytes = mss.tools.to_png(i.rgb, i.size)
        img = PIL.Image.open(io.BytesIO(image_bytes))
        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)
        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_screen(self):
        while True:
            frame = await asyncio.to_thread(self._get_screen)
            if frame is None:
                break
            await asyncio.sleep(1.0)
            await self.out_queue.put(frame)

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)

    async def listen_audio(self):
        mic_info = pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        kwargs = {"exception_on_overflow": False} if __debug__ else {}
        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def receive_audio(self):
        while True:
            async for response in self.session.receive():
                if data := response.data:
                    self.audio_in_queue.put_nowait(data)
                    continue
                if text := response.text:
                    print(text, end="")
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while True:
            bytestream = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, bytestream)

    async def run(self):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)
                tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                if self.video_mode == "camera":
                    tg.create_task(self.get_frames())
                elif self.video_mode == "screen":
                    tg.create_task(self.get_screen())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())
        except Exception:
            print("Error occurred:", traceback.format_exc())

# Run the loop if this file is executed directly
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default=DEFAULT_MODE, choices=["camera", "screen"])
    args = parser.parse_args()
    audio_loop = AudioLoop(video_mode=args.mode)
    asyncio.run(audio_loop.run())


















