"""
Darija → English Audio Translator
A Streamlit app that transcribes Moroccan Arabic (Darija) audio
and translates it to English using Whisper + Claude.
"""

import streamlit as st
import tempfile
import os
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Darija → English Translator",
    page_icon="🇲🇦",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Custom CSS for a clean, modern look
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main container */
    .stApp { max-width: 800px; margin: 0 auto; }

    /* Header styling */
    .main-header {
        text-align: center;
        padding: 1.5rem 0 1rem;
    }
    .main-header h1 {
        font-size: 2rem;
        margin-bottom: 0.25rem;
    }
    .main-header p {
        color: #888;
        font-size: 1rem;
    }

    /* Result cards */
    .result-card {
        border: 1px solid var(--faded-text-color, #e0e0e0);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        background: var(--secondary-background-color, #fafafa);
        color: var(--text-color, #000000);
    }
    .result-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--faded-text-color, #888888);
        margin-bottom: 0.5rem;
    }
    .result-text {
        font-size: 1.1rem;
        line-height: 1.6;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .status-success { background: #d4edda; color: #155724; }
    .status-processing { background: #fff3cd; color: #856404; }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🇲🇦 Darija → English</h1>
    <p>Upload or record Moroccan Arabic audio and get an English translation</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar: API key configuration
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    st.subheader("API Keys")
    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="For Whisper speech-to-text. Get one at platform.openai.com",
        placeholder="sk-...",
    )
    anthropic_key = st.text_input(
        "Anthropic API Key (Optional)",
        type="password",
        help="For Claude translation. If not provided, the app will use OpenAI GPT-4o instead.",
        placeholder="sk-ant-...",
    )

    st.divider()
    st.subheader("Translation options")
    translation_engine = st.radio(
        "Translation engine",
        options=["OpenAI (GPT-4o)", "Anthropic (Claude)"],
        index=0 if not anthropic_key else 1,
        help="OpenAI uses only your OpenAI key. Anthropic requires a separate key.",
    )
    formality = st.select_slider(
        "Translation style",
        options=["Very casual", "Casual", "Neutral", "Formal", "Very formal"],
        value="Neutral",
    )
    include_transliteration = st.checkbox(
        "Show transliteration",
        value=True,
        help="Show a Latin-script version of the Darija text",
    )
    include_context = st.checkbox(
        "Show cultural context",
        value=True,
        help="Explain idioms, slang, and cultural references",
    )

    st.divider()
    st.caption(
        "Your API keys are never stored. They stay in your browser session only."
    )


# ---------------------------------------------------------------------------
# Helper: Transcribe audio with Whisper
# ---------------------------------------------------------------------------
def transcribe_audio(audio_path: str, api_key: str) -> dict:
    """Send audio to OpenAI Whisper API and return transcription."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ar",  # Forcing Arabic prevents Whisper from misidentifying Darija as French/Spanish
            prompt="Wakha, danya hanya, bghit, bezzaf, chwiya, mezian, khouya, sahbi, oui, d'accord, c'est bon, merci, chouf, brit, daba, maghrib, darija", # Guide Whisper for Darija/French
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    return {
        "text": response.text,
        "segments": [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
            }
            for seg in (response.segments or [])
        ],
        "duration": response.duration,
    }


# ---------------------------------------------------------------------------
# Helper: Translate Darija text to English
# ---------------------------------------------------------------------------
def translate_darija(
    darija_text: str,
    openai_key: str,
    anthropic_key: str = None,
    engine: str = "OpenAI (GPT-4o)",
    formality: str = "Neutral",
    include_transliteration: bool = True,
    include_context: bool = True,
) -> dict:
    """Translate Darija text to English using either Claude or GPT-4o."""
    # Build the prompt with optional sections
    optional_sections = ""
    if include_transliteration:
        optional_sections += """
- "transliteration": A Latin-script (Franco-Arabic / Arabizi) representation of the Darija text so non-Arabic readers can see how it sounds."""
    if include_context:
        optional_sections += """
- "cultural_notes": A brief explanation of any idioms, slang, French/Spanish loanwords, or cultural context that would help an English speaker fully understand the meaning. If there's nothing notable, set this to null."""

    system_prompt = f"""You are an expert translator specializing in Moroccan Darija (الدارجة المغربية).
You understand the unique characteristics of Darija including:
- Its blend of Arabic, French, Amazigh (Berber), and Spanish vocabulary
- Code-switching between Darija and French (very common in Morocco)
- Moroccan idioms, proverbs, and cultural expressions
- Regional variations across Morocco

CRITICALLY IMPORTANT: The input text is a machine transcription (from Whisper) and may contain errors. 
Whisper often mishears Darija words or hallucinates Standard Arabic (MSA) words that sound similar. 
You must use your knowledge of Darija context to infer the *intended* meaning and silently correct transcription errors before translating.

Examples of Darija translation:
- "شنو درتي البارح؟" -> "What did you do yesterday?"
- "راه مشى بحالو" -> "He has already left."
- "واخا، غادي نمشي دابا" -> "Okay, I'll go now."
- "صافي، مزيان" -> "Alright, good (or fine)."
- "سي بون" (C'est bon) -> "It's good/okay."

Your translation style should be: {formality}

Respond ONLY with valid JSON (no markdown, no backticks) in this exact format:
{{
    "translation": "The English translation of the text",
    "detected_language_mix": "What languages appear in the input (e.g. 'Darija with French phrases')",
    "confidence": "high/medium/low"{f',{optional_sections}' if optional_sections else ''}
}}"""

    if engine == "Anthropic (Claude)" and anthropic_key:
        import anthropic

        client = anthropic.Anthropic(api_key=anthropic_key)
        model = "claude-3-5-sonnet-latest"
        
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            temperature=0.1,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Translate this Darija text to English:\n\n{darija_text}",
                }
            ],
        )
        response_text = message.content[0].text
    else:
        # Default to OpenAI GPT-4o
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        
        message = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Translate this Darija text to English:\n\n{darija_text}"}
            ]
        )
        response_text = message.choices[0].message.content

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If Claude returns markdown-wrapped JSON, strip it
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Helper: Translate with timestamps (for subtitles)
# ---------------------------------------------------------------------------
def translate_segments(
    segments: list, 
    openai_key: str, 
    anthropic_key: str = None, 
    engine: str = "OpenAI (GPT-4o)", 
    formality: str = "Neutral"
) -> list:
    """Translate each segment individually for subtitle-style output."""

    # Batch all segments into one call for efficiency
    segments_text = "\n".join(
        f"[{i}] {seg['text']}" for i, seg in enumerate(segments)
    )

    if engine == "Anthropic (Claude)" and anthropic_key:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=2048,
            temperature=0.1,
            system=f"""You are an expert Darija-to-English translator. The input is a transcription that may contain errors (e.g., misheard Darija or hallucinated Standard Arabic). Correct these silently based on context.
Translate each numbered line.
Translation style: {formality}
Respond ONLY with valid JSON (no markdown): a JSON array of objects with "index" and "translation" fields.""",
            messages=[
                {
                    "role": "user",
                    "content": f"Translate each line:\n\n{segments_text}",
                }
            ],
        )
        response_text = message.content[0].text
    else:
        # OpenAI fallback
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        
        message = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.1,
            messages=[
                {"role": "system", "content": f"""You are an expert Darija-to-English translator. The input is a transcription that may contain errors (e.g., misheard Darija or hallucinated Standard Arabic). Correct these silently based on context.
Translate each numbered line.
Translation style: {formality}
Respond ONLY with valid JSON (no markdown): a JSON array of objects with "index" and "translation" fields."""},
                {"role": "user", "content": f"Translate each line:\n\n{segments_text}"}
            ]
        )
        response_text = message.choices[0].message.content
    try:
        translations = json.loads(response_text)
    except json.JSONDecodeError:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        translations = json.loads(cleaned)

    # Merge translations with timestamps
    result = []
    trans_map = {t["index"]: t["translation"] for t in translations}
    for i, seg in enumerate(segments):
        result.append(
            {
                "start": seg["start"],
                "end": seg["end"],
                "darija": seg["text"],
                "english": trans_map.get(i, "[translation unavailable]"),
            }
        )
    return result


# ---------------------------------------------------------------------------
# Helper: Generate SRT subtitle file
# ---------------------------------------------------------------------------
def generate_srt(segments: list) -> str:
    """Generate SRT subtitle content from translated segments."""

    def format_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{format_time(seg['start'])} --> {format_time(seg['end'])}")
        lines.append(seg["english"])
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main UI: Input method tabs
# ---------------------------------------------------------------------------
tab_upload, tab_record = st.tabs(["📁 Upload audio", "🎙️ Record audio"])

audio_path = None

with tab_upload:
    uploaded_file = st.file_uploader(
        "Drop an audio or video file here",
        type=["mp3", "wav", "m4a", "ogg", "flac", "mp4", "webm", "mpeg", "mpga"],
        help="Supports most audio formats. Max 25MB for Whisper API.",
    )
    if uploaded_file:
        st.audio(uploaded_file)
        # Save to temp file
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            audio_path = tmp.name

with tab_record:
    recorded = st.audio_input("Click to start recording")
    if recorded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(recorded.getbuffer())
            audio_path = tmp.name


# ---------------------------------------------------------------------------
# Translation mode
# ---------------------------------------------------------------------------
if audio_path:
    st.divider()
    mode = st.radio(
        "Output format",
        ["Full translation", "Subtitles (with timestamps)"],
        horizontal=True,
    )

    translate_btn = st.button("🚀 Translate", type="primary", use_container_width=True)

    if translate_btn:
        # Validate API keys
        if not openai_key:
            st.error("Please add your OpenAI API key in the sidebar.")
            st.stop()
        if translation_engine == "Anthropic (Claude)" and not anthropic_key:
            st.error("Please add your Anthropic API key to use Claude.")
            st.stop()

        # Step 1: Transcribe
        with st.status("🎧 Transcribing Darija audio...", expanded=True) as status:
            try:
                st.write("Sending audio to Whisper...")
                transcription = transcribe_audio(audio_path, openai_key)
                st.write(
                    f"✅ Transcribed {transcription.get('duration', '?')}s of audio"
                )
                status.update(label="✅ Transcription complete", state="complete")
            except Exception as e:
                status.update(label="❌ Transcription failed", state="error")
                st.error(f"Whisper error: {e}")
                st.stop()

        # Show raw transcription
        st.markdown("#### Darija transcription")
        st.markdown(
            f"""<div class="result-card">
            <div class="result-label">Original (Arabic script)</div>
            <div class="result-text" dir="rtl" lang="ar">{transcription['text']}</div>
        </div>""",
            unsafe_allow_html=True,
        )

        # Step 2: Translate
        if mode == "Full translation":
            with st.status("🌍 Translating to English...", expanded=True) as status:
                try:
                    st.write("Sending to Claude for translation...")
                    result = translate_darija(
                        transcription["text"],
                        openai_key,
                        anthropic_key,
                        translation_engine,
                        formality,
                        include_transliteration,
                        include_context,
                    )
                    status.update(label="✅ Translation complete", state="complete")
                except Exception as e:
                    status.update(label="❌ Translation failed", state="error")
                    st.error(f"Translation error: {e}")
                    st.stop()

            # Display results
            st.markdown("#### English translation")
            st.markdown(
                f"""<div class="result-card">
                <div class="result-label">English</div>
                <div class="result-text">{result['translation']}</div>
            </div>""",
                unsafe_allow_html=True,
            )

            # Transliteration
            if include_transliteration and result.get("transliteration"):
                st.markdown(
                    f"""<div class="result-card">
                    <div class="result-label">Transliteration (how it sounds)</div>
                    <div class="result-text" style="font-style: italic;">{result['transliteration']}</div>
                </div>""",
                    unsafe_allow_html=True,
                )

            # Metadata row
            col1, col2 = st.columns(2)
            with col1:
                lang_mix = result.get("detected_language_mix", "Darija")
                st.caption(f"🗣️ Detected: {lang_mix}")
            with col2:
                confidence = result.get("confidence", "unknown")
                emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(
                    confidence, "⚪"
                )
                st.caption(f"{emoji} Confidence: {confidence}")

            # Cultural context
            if include_context and result.get("cultural_notes"):
                with st.expander("📚 Cultural context & notes"):
                    st.write(result["cultural_notes"])

        else:
            # Subtitle mode
            if not transcription.get("segments"):
                st.warning(
                    "No timestamp segments found. Try 'Full translation' instead."
                )
                st.stop()

            with st.status(
                "🌍 Translating segments...", expanded=True
            ) as status:
                try:
                    st.write(
                        f"Translating {len(transcription['segments'])} segments..."
                    )
                    translated_segments = translate_segments(
                        transcription["segments"], 
                        openai_key, 
                        anthropic_key, 
                        translation_engine, 
                        formality
                    )
                    status.update(label="✅ Subtitles ready", state="complete")
                except Exception as e:
                    status.update(label="❌ Translation failed", state="error")
                    st.error(f"Translation error: {e}")
                    st.stop()

            # Display subtitle table
            st.markdown("#### Translated subtitles")
            for seg in translated_segments:
                start = f"{seg['start']:.1f}s"
                end = f"{seg['end']:.1f}s"
                st.markdown(
                    f"""<div class="result-card" style="padding: 0.75rem 1rem;">
                    <span style="color: #888; font-size: 0.8rem;">{start} → {end}</span><br/>
                    <span dir="rtl" style="color: #999;">{seg['darija']}</span><br/>
                    <span>{seg['english']}</span>
                </div>""",
                    unsafe_allow_html=True,
                )

            # Download SRT
            srt_content = generate_srt(translated_segments)
            st.download_button(
                "⬇️ Download .srt subtitle file",
                data=srt_content,
                file_name="darija_translation.srt",
                mime="text/plain",
                use_container_width=True,
            )

        # Cleanup temp file
        try:
            os.unlink(audio_path)
        except OSError:
            pass

# ---------------------------------------------------------------------------
# Footer with tips
# ---------------------------------------------------------------------------
st.divider()
with st.expander("💡 Tips for best results"):
    st.markdown("""
- **Clear audio matters**: Reduce background noise for more accurate transcription.
- **Whisper handles French code-switching well**: If the speaker mixes Darija and French (very common!), it will still pick up both.
- **Longer audio = better context**: Whisper and Claude both perform better with more context. Short phrases can be ambiguous.
- **Try different formality levels**: "Casual" captures the vibe of street Darija, while "Formal" gives you cleaner English.
- **File size limit**: The Whisper API accepts files up to 25MB. For longer recordings, consider splitting them first.
    """)
