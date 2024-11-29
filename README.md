# Viral Scripts - README

## Overview
Viral Scripts is a Flask-based web app for repurposing video content. It lets you extract transcripts from YouTube, Instagram, and TikTok videos, reformat them for readability, and rehash them for new audiences or niches.

---

## Features
**1. Video Transcript Extraction**:
Extracts transcripts from YouTube videos using the YouTube API.
Transcribes audio locally for TikTok and Instagram videos.

**2. Transcript Formatting:**
Formats transcripts into readable formats for Google Docs.
Keeps the original sentence structure while enhancing readability.

**3. Rehashing:**
Rehashes transcripts to keep the same structure but modify the wording.
Customizes transcripts for different niches or topics.

**4. Multi-Platform Support:**
Compatible with YouTube, Instagram, and TikTok video URLs.

---

## Requirements
1. **Python**: Version 3.8 or higher.
2. **Libraries**:
   - Flask
   - instaloader
   - yt_dlp
   - youtube-transcript-api
   - whisper
   - requests
   - openai
3. **API Keys**:
   - OpenAI API Key
   - YouTube API Key
4. **Additional Tools**:
   - FFmpeg for audio processing.

---

## Installation
1. Clone this repository.
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```
2. Install dependencies.
   ```bash
   pip install -r requirements.txt
   ```
3. Set up a `.env` file with your API keys.
   ```env
   OPENAI_API_KEY=your_openai_api_key
   YOUTUBE_API_KEY=your_youtube_api_key
   ```
4. Run the application.
   ```bash
   python app.py
   ```

---

## Usage
1. Open the app in your browser at `http://127.0.0.1:5000`.
2. Enter a video URL (YouTube, TikTok, or Instagram).
3. Click **Get Transcript** to extract the transcript.
4. Use:
   - **Rehash**: Modify wording while retaining structure.
   - **Rehash for Different Niche**: Tailor the transcript for a new topic.

---

## File Structure
```
.
├── app.py           # Main Flask app entry point
├── config.py        # Configuration file for API keys and environment variables
├── routes.py        # Defines routes for the application
├── utils.py         # Helper functions for video and transcript processing
├── templates/       # HTML templates for the app
│   ├── index.html   # Main interface
│   ├── error.html   # Error display
│   ├── rehashed.html # Rehashed transcript display
└── requirements.txt # Required libraries
```

---

## Known Issues
- Instagram and TikTok support is limited to video content.
- Transcript quality may vary depending on video clarity and language.

---

## Contributing
1. Fork the repository.
2. Create a feature branch.
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes.
   ```bash
   git commit -m "Add new feature"
   ```
4. Push to the branch.
   ```bash
   git push origin feature-name
   ```
5. Submit a pull request.

---

## License
This project is licensed under the [MIT License](LICENSE).

