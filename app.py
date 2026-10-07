import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from services.ai_service import generate_script, generate_voiceover
from services.video_service import generate_video_from_script
from services.youtube_service import upload_to_youtube

load_dotenv()

st.set_page_config(page_title="YouTube Automation Studio", page_icon="🎬", layout="wide")


st.title("🎬 YouTube Automation Studio")
st.caption("Simple AI workflow for Shorts, facts videos, and documentary-style content")

with st.sidebar:
    st.header("API Keys")
    st.text_input("OpenAI API Key", key="openai_api_key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    st.text_input("ElevenLabs API Key", key="elevenlabs_api_key", type="password", value=os.getenv("ELEVENLABS_API_KEY", ""))
    st.text_input("YouTube Client ID", key="youtube_client_id", value=os.getenv("YOUTUBE_CLIENT_ID", ""))
    st.text_input("YouTube Client Secret", key="youtube_client_secret", type="password", value=os.getenv("YOUTUBE_CLIENT_SECRET", ""))

    st.markdown("---")
    st.info(
        "This app creates a full starter pipeline: script → voiceover → visual scenes → export → optional YouTube upload."
    )


template_map = {
    "Shorts": "Fast hook, punchy lines, quick facts, strong ending.",
    "News / Facts": "Clear sequence, numbered points, easy explanations, concise narration.",
    "Documentary": "Detailed storytelling, transitions, scene-based narration, rich context.",
    "Sticky Character": "Friendly motion-graphic style with hook, explanation, and strong recap.",
}

with st.form("video_form"):
    st.subheader("1) Content setup")
    topic = st.text_input("Video topic", placeholder="Example: 5 little-known facts about black holes")
    content_type = st.selectbox("Content type", ["Shorts", "News / Facts", "Documentary", "Sticky Character"])
    tone = st.selectbox("Tone", ["Educational", "Casual", "Powerful", "Storytelling", "News-style"])
    language = st.selectbox("Language", ["English", "Hindi", "Spanish", "French", "Arabic"])
    video_length = st.slider("Target length (minutes)", min_value=0.5, max_value=8.0, value=2.0, step=0.5)
    voice = st.selectbox("Voice style", ["Female", "Male", "Neutral"])

    st.markdown("---")
    st.subheader("2) Output options")
    add_captions = st.checkbox("Add styled captions / scene titles", value=True)
    auto_upload = st.checkbox("Auto-upload to YouTube if credentials are configured", value=False)

    submitted = st.form_submit_button("Generate video")

if submitted:
    if not topic:
        st.warning("Please enter a video topic first.")
        st.stop()

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    with st.spinner("Creating your script, voiceover, and video..."):
        script = generate_script(
            topic=topic,
            tone=tone,
            style=content_type,
            language=language,
            duration_minutes=video_length,
            api_key=st.session_state.get("openai_api_key", ""),
        )

        st.success("Script generated.")
        st.markdown("### Script preview")
        st.write(script)

        voice_path = generate_voiceover(
            text=script,
            output_path=str(output_dir / "voiceover.mp3"),
            language=language,
            voice=voice.lower(),
            elevenlabs_api_key=st.session_state.get("elevenlabs_api_key", ""),
        )

        final_video = output_dir / "final_video.mp4"
        generate_video_from_script(
            script=script,
            audio_path=voice_path,
            output_path=str(final_video),
            style=content_type,
            captions=add_captions,
        )

        if auto_upload:
            result = upload_to_youtube(
                video_path=str(final_video),
                title=f"{topic} | {content_type}",
                description=(
                    f"Generated with YouTube Automation Studio\n\n"
                    f"Topic: {topic}\n"
                    f"Style: {content_type}\n"
                    f"Tone: {tone}\n"
                    f"Language: {language}"
                ),
                client_id=st.session_state.get("youtube_client_id", ""),
                client_secret=st.session_state.get("youtube_client_secret", ""),
            )
            st.info(f"Upload result: {result.get('status', 'unknown')} - {result.get('message', '')}")

        st.markdown("---")
        st.subheader("Download")
        with open(final_video, "rb") as f:
            st.download_button(
                label="Download final video",
                data=f.read(),
                file_name="final_video.mp4",
                mime="video/mp4",
            )

        st.subheader("Generated files")
        st.code(
            f"Script: {output_dir / 'script.txt'}\n"
            f"Voiceover: {voice_path}\n"
            f"Video: {final_video}",
            language="text",
        )

else:
    st.info("Fill in your content details and click 'Generate video'.")

    st.markdown("### Recommended workflow")
    st.markdown(
        """
        1. Enter a topic.
        2. Pick your style: Shorts, Facts, Documentary, or Sticky Character.
        3. Generate the full AI workflow.
        4. Download or upload to YouTube.
        """
    )

    st.markdown("### Content templates")
    for key, value in template_map.items():
        with st.container():
            st.markdown(f"**{key}**: {value}")

    st.markdown("### Example prompts")
    st.code(
        "Top 5 hidden facts about the moon\n"
        "Why your brain creates shortcuts\n"
        "The strange history of social media\n"
        "3 surprising inventions from the 1800s",
        language="text",
    )


if __name__ == "__main__":
    pass
