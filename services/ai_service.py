import os
import re
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _build_fallback_script(topic: str, tone: str, style: str, language: str, duration_minutes: float) -> str:
    style_name = style.lower()
    hook = f"Did you know this about {topic}?"

    sections = [
        f"{hook}",
        f"Welcome back, and today we're exploring {topic}. This topic is interesting because it changes how we see the world.",
        f"First, the big idea: {topic} is more than a headline. It connects to everyday life, hidden patterns, and important lessons.",
        f"Next, here are 3 key points to remember. Number one: the context matters. Number two: the timing matters. Number three: the impact matters.",
        f"In conclusion, {topic} is a reminder that the world is packed with details most people miss. If you liked this video, subscribe for more breakdowns.",
    ]

    intro = "\n\n".join(sections)
    if style_name == "shorts":
        intro = intro[:600]
    return intro


def generate_script(
    topic: str,
    tone: str,
    style: str,
    language: str,
    duration_minutes: float,
    api_key: str | None = None,
) -> str:
    """Generate script text. Uses OpenAI if a key is available, otherwise fallback."""
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            prompt = (
                f"Create a compelling {tone.lower()} {style.lower()} script in {language} about: {topic}. "
                f"The video should be approximately {duration_minutes} minutes long. "
                "Write a captivating hook, 3-5 scenes, and a strong conclusion."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a YouTube script writer. Write concise, engaging scenes."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
            )
            script = response.choices[0].message.content.strip()
            if script:
                script_path = os.path.join("output", "script.txt")
                os.makedirs("output", exist_ok=True)
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(script)
                return script
        except Exception:
            pass

    script = _build_fallback_script(topic, tone, style, language, duration_minutes)
    os.makedirs("output", exist_ok=True)
    with open(os.path.join("output", "script.txt"), "w", encoding="utf-8") as f:
        f.write(script)
    return script


def generate_voiceover(
    text: str,
    output_path: str,
    language: str = "English",
    voice: str = "female",
    elevenlabs_api_key: str | None = None,
) -> str:
    """Create voiceover audio using ElevenLabs or gTTS fallback."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    lang_map = {
        "English": "en",
        "Hindi": "hi",
        "Spanish": "es",
        "French": "fr",
        "Arabic": "ar",
    }
    lang_code = lang_map.get(language, "en")

    if elevenlabs_api_key:
        try:
            import requests

            voice_name = "Rachel" if voice == "female" else "George" if voice == "male" else "Bella"
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            }
            headers = {
                "Content-Type": "application/json",
                "xi-api-key": elevenlabs_api_key,
            }
            response = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_name}",
                headers=headers,
                json=payload,
                timeout=120,
            )
            if response.ok:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
        except Exception:
            pass

    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(output_path)
        return output_path
    except Exception as exc:
        raise RuntimeError(f"Unable to generate audio. Error: {exc}") from exc
