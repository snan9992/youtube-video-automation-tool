import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from services.ai_service import generate_script, generate_voiceover
from services.video_service import generate_video_from_script
from services.youtube_service import upload_to_youtube

load_dotenv()

st.set_page_config(page_title="YouTube Automation Studio Pro", page_icon="🎬", layout="wide")

st.title("🎬 YouTube Automation Studio Pro")
st.caption("Full AI content pipeline for Shorts, fact videos, documentaries, and sticky-character explainers")

with st.sidebar:
    st.header("API Access")
    st.text_input("OpenAI API Key", key="openai_api_key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    st.text_input("ElevenLabs API Key", key="elevenlabs_api_key", type="password", value=os.getenv("ELEVENLABS_API_KEY", ""))
    st.text_input("YouTube Client ID", key="youtube_client_id", value=os.getenv("YOUTUBE_CLIENT_ID", ""))
    st.text_input("YouTube Client Secret", key="youtube_client_secret", type="password", value=os.getenv("YOUTUBE_CLIENT_SECRET", ""))
    st.markdown("---")
    st.info("This version includes premium workflow controls: templates, batch processing, subtitle export, music layering, and upload support.")

TEMPLATE_GUIDES = {
    "Shorts": "Fast hook, quick timeline, punchy facts, strong CTA.",
    "News / Facts": "Lead with the factual question, then explain with numbered points and clear recap.",
    "Documentary": "Use narrative structure, context, big-idea framing, and emotional payoff.",
    "Sticky Character": "Use a relatable voice, simple analogies, and clear story progression.",
    "Brand Story": "Position the topic around value, problem, solution, proof, and CTA.",
    "Explainer": "Use a simple concept breakdown with logical flow and memorable close.",
}

with st.form("video_form"):
    st.subheader("1) Content setup")
    input_mode = st.radio("Input mode", ["Single topic", "Batch topics (one per line)"])

    if input_mode == "Single topic":
        topic_value = st.text_input("Video topic", placeholder="Example: 5 little-known facts about black holes")
    else:
        topic_value = st.text_area(
            "Topics (one per line)",
            height=180,
            placeholder="Top 5 hidden facts about the moon\nWhy your brain creates shortcuts\nThe strange history of social media",
        )

    content_type = st.selectbox("Content template", list(TEMPLATE_GUIDES.keys()))
    tone = st.selectbox("Tone", ["Educational", "Casual", "Powerful", "Storytelling", "News-style"])
    language = st.selectbox("Language", ["English", "Hindi", "Spanish", "French", "Arabic"])
    video_length = st.slider("Target length (minutes)", min_value=0.5, max_value=8.0, value=2.0, step=0.5)
    voice = st.selectbox("Voice style", ["Female", "Male", "Neutral"])

    st.markdown("---")
    st.subheader("2) Production settings")
    add_captions = st.checkbox("Add styled subtitles / scene overlays", value=True)
    export_srt = st.checkbox("Export SRT subtitle file", value=True)
    auto_upload = st.checkbox("Auto-upload to YouTube if credentials are present", value=False)
    music_file = st.file_uploader("Optional background music (.mp3/.wav/.m4a)", type=["mp3", "wav", "m4a"], accept_multiple_files=False)
    music_volume = st.slider("Background music volume", min_value=0.0, max_value=0.5, value=0.12, step=0.01)
    add_intro_outro = st.checkbox("Add intro/outro label cards", value=True)

    submitted = st.form_submit_button("Generate video(s)")

if submitted:
    if input_mode == "Single topic":
        topics = [topic_value.strip()] if topic_value.strip() else []
    else:
        topics = [line.strip() for line in topic_value.splitlines() if line.strip()]

    if not topics:
        st.warning("Please enter at least one topic before generating a video.")
        st.stop()

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    music_path = None
    if music_file is not None:
        music_path = output_dir / f"music_{music_file.name}"
        music_path.write_bytes(music_file.getvalue())
        music_path = str(music_path)

    generated_results = []

    with st.spinner("Generating your video pipeline..."):
        for idx, topic in enumerate(topics, start=1):
            safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", topic.strip()).strip("_") or f"video_{idx}"
            topic_dir = output_dir / safe_name
            topic_dir.mkdir(exist_ok=True)

            script = generate_script(
                topic=topic,
                tone=tone,
                style=content_type,
                language=language,
                duration_minutes=video_length,
                api_key=st.session_state.get("openai_api_key", ""),
            )

            voice_path = generate_voiceover(
                text=script,
                output_path=str(topic_dir / "voiceover.mp3"),
                language=language,
                voice=voice.lower(),
                elevenlabs_api_key=st.session_state.get("elevenlabs_api_key", ""),
            )

            subtitle_path = topic_dir / "captions.srt" if export_srt else None
            final_video = topic_dir / "final_video.mp4"

            generate_video_from_script(
                script=script,
                audio_path=voice_path,
                output_path=str(final_video),
                style=content_type,
                captions=add_captions,
                subtitle_path=str(subtitle_path) if subtitle_path else None,
                music_path=music_path,
                music_volume=music_volume,
                intro_outro=add_intro_outro,
            )

            if auto_upload:
                upload_result = upload_to_youtube(
                    video_path=str(final_video),
                    title=f"{topic} | {content_type}",
                    description=(
                        f"Generated with YouTube Automation Studio Pro\n\n"
                        f"Topic: {topic}\n"
                        f"Style: {content_type}\n"
                        f"Tone: {tone}\n"
                        f"Language: {language}"
                    ),
                    client_id=st.session_state.get("youtube_client_id", ""),
                    client_secret=st.session_state.get("youtube_client_secret", ""),
                )
            else:
                upload_result = {"status": "skipped", "message": "Auto-upload off"}

            generated_results.append(
                {
                    "topic": topic,
                    "script": script,
                    "final_video": str(final_video),
                    "subtitle": str(subtitle_path) if subtitle_path else "Not exported",
                    "upload": upload_result,
                }
            )

            st.markdown(f"### #{idx}: {topic}")
            st.write(f"Upload: {upload_result.get('status', 'unknown')} - {upload_result.get('message', '')}")

            with open(final_video, "rb") as f:
                st.download_button(
                    label=f"Download video #{idx}",
                    data=f.read(),
                    file_name=f"{safe_name}.mp4",
                    mime="video/mp4",
                    key=f"download_{idx}",
                )

            if subtitle_path and subtitle_path.exists():
                with open(subtitle_path, "r", encoding="utf-8") as f:
                    st.caption("SRT subtitle preview")
                    st.code(f.read()[:600], language="text")

    st.success(f"Completed generation for {len(generated_results)} topic(s).")

else:
    st.info("Enter your topic(s) and click 'Generate video(s)'.")

    st.markdown("### Production workflow")
    st.markdown(
        """
        1. Add one topic or a batch of topics.
        2. Select a professional template.
        3. Generate script + voice + visuals.
        4. Export subtitles and download final video(s).
        5. Optionally upload directly to YouTube.
        """
    )

    st.markdown("### Template guide")
    for name, guide in TEMPLATE_GUIDES.items():
        st.markdown(f"**{name}**: {guide}")

    st.markdown("### Example batch inputs")
    st.code(
        "Top 5 hidden facts about the moon\n"
        "Why your brain creates shortcuts\n"
        "3 surprising inventions from the 1800s\n"
        "The strange history of social media",
        language="text",
    )

if __name__ == "__main__":
    pass
