# 🇲🇦 Darija → English Audio Translator

Translate Moroccan Arabic (Darija) audio to English using AI.

**How it works:**
1. You upload or record Darija audio
2. OpenAI Whisper transcribes the speech to text
3. Claude translates the Darija text to English
4. You get the translation with optional transliteration and cultural notes

## Quick start

### 1. Install Python

If you don't have Python yet, download it from [python.org](https://www.python.org/downloads/). Version 3.9 or higher.

### 2. Get your API keys

You'll need two API keys (both have free tiers or trial credits):

- **OpenAI API key** (for Whisper speech-to-text): Sign up at [platform.openai.com](https://platform.openai.com)
- **Anthropic API key** (for Claude translation): Sign up at [console.anthropic.com](https://console.anthropic.com)

### 3. Set up the project

Open a terminal and run:

```bash
# Clone or download this folder, then:
cd darija-translator

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

### 4. Add your API keys

Paste your OpenAI and Anthropic API keys into the sidebar of the app. They're only stored in your browser session and never saved anywhere.

## Features

- **Upload audio**: Supports MP3, WAV, M4A, OGG, FLAC, MP4, and more
- **Record live**: Click the microphone button to record directly in the browser
- **Full translation**: Get the complete English translation with confidence scores
- **Subtitle mode**: Get timestamped translations you can download as an .srt file
- **Transliteration**: See the Darija text in Latin script (Franco-Arabic / Arabizi)
- **Cultural context**: Explanations of idioms, slang, and French/Spanish loanwords
- **Adjustable formality**: From street-casual to formal, depending on your needs

## Cost estimate

- **Whisper API**: ~$0.006 per minute of audio
- **Claude API**: ~$0.01-0.03 per translation (depending on length)
- A typical 1-minute voice note costs about 2-3 cents total

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "ModuleNotFoundError" | Run `pip install -r requirements.txt` again |
| Whisper returns garbled text | Make sure the audio is clear, try a longer clip for more context |
| Translation looks off | Try adjusting the formality slider, or check if the transcription step was accurate first |
| File too large | Whisper API limit is 25MB. Split longer files with a tool like Audacity |

## How Darija translation works

Darija is uniquely challenging because it is not just "Arabic with an accent." It blends:
- Moroccan Arabic as the base
- French vocabulary (from colonial history, still widely used)
- Amazigh (Berber) words and structures
- Spanish loanwords (especially in northern Morocco)

Traditional translation tools like Google Translate treat Darija as standard Arabic and miss most of this. This app uses an LLM (Claude) which understands code-switching and cultural context, giving you much more accurate results.

## License

MIT. Use it however you want.
