import os
import re
from typing import List

from dotenv import load_dotenv

load_dotenv()

STYLE_BLUEPRINTS = {
    "Shorts": {
        "hook": "Start with a shocking fact or curiosity question.",
        "body": "Deliver 3 short punchy points with visual transitions.",
        "ending": "Finish with a strong takeaway and CTA.",
    },
    "News / Facts": {
        "hook": "Lead with a clear statement and the main question.",
        "body": "Present numbered facts with quick explanations and context.",
        "ending": "Summarize key insights and invite discussion.",
    },
    "Documentary": {
        "hook": "Open with a narrative hook or historical frame.",
        "body": "Build a story arc with cause, context, impact, and evidence.",
        "ending": "Close with reflection and a memorable takeaway.",
    },
    "Sticky Character": {
        "hook": "Use a relatable character voice and a clear curiosity gap.",
        "body": "Explain the concept through simple scenes, analogies, and reactions.",
        "ending": "Wrap up with a clear summary, emotional payoff, and call to action.",
    },
}


def _build_fallback_script(topic: str, tone: str, style: str, language: str, duration_minutes: float) -> str:
    blueprint = STYLE_BLUEPRINTS.get(style, STYLE_BLUEPRINTS["Shorts"])
    style_name = style.lower()

    intro_line = f"Did you know this about {topic}?"
    hook = blueprint["hook"]
    body = blueprint["body"]
    ending = blueprint["ending"]

    sections = [
        f"{intro_line}\n\n{hook}",
        f"Welcome back. Today we’re looking at {topic} from a {tone.lower()} angle.",
        f"The big idea: {topic} matters because it affects how people think, behave, and react in real life.",
        f"Here are three key moments to remember. First, the background. Second, the surprise. Third, the real-life impact.",
        f"{body}",
        f"{ending}\n\nIn summary, {topic} is a reminder that the details often matter more than the headline. If you found this useful, like, follow, and subscribe for more video breakdowns.",
    ]

    script = "\n\n".join(sections)
    if style_name == "shorts":
        return script[:800]
    return script


def _build_openai_prompt(topic: str, tone: str, style: str, language: str, duration_minutes: float) -> str:
    blueprint = STYLE_BLUEPRINTS.get(style, STYLE_BLUEPRINTS["Shorts"])
    return (
        f"Write a high-retention YouTube video script in {language} on the topic: {topic}.\n"
        f"Style: {style}. Tone: {tone}. Length target: {duration_minutes} minutes.\n"
        f"Use this structure: 1) Strong hook 2) Backstory/context 3) 3 clear points 4) Emotional or factual payoff 5) Ending CTA.\n"
        f"Creative direction: {blueprint['hook']} | {blueprint['body']} | {blueprint['ending']}\n"
        "Make it natural, engaging, and suited for short-form or documentary storytelling. Return only the script text."
    )


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
            prompt = _build_openai_prompt(topic, tone, style, language, duration_minutes)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a high-performing YouTube scriptwriter for AI video automation."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.85,
            )
            script = response.choices[0].message.content.strip()
            if script:
                os.makedirs("output", exist_ok=True)
                with open(os.path.join("output", "script.txt"), "w", encoding="utf-8") as f:
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

            voice_name = "Rachel" if voice.lower() == "female" else "George" if voice.lower() == "male" else "Bella"
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
