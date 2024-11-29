import re
import logging
import openai
from flask import Flask, request, render_template_string
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
import os
import subprocess

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get your OpenAI API key from the .env file
openai.api_key = os.getenv('OPENAI_API_KEY')

def get_video_id(url):
    """
    Extract the video ID from a YouTube URL.
    """
    try:
        video_id_match = re.search(r'(?<=v=)[^&#]+|(?<=youtu.be/)[^?&#]+|(?<=shorts/)[^?&#]+', url)
        if video_id_match:
            video_id = video_id_match.group(0)
            logger.debug(f"Extracted video ID: {video_id}")
            return video_id
        else:
            raise ValueError("Invalid YouTube URL provided.")
    except Exception as e:
        logger.error(f"Error extracting video ID: {e}")
        raise

def fetch_transcript(video_id, language='en'):
    """
    Fetch the transcript of the given YouTube video ID.
    """
    try:
        logger.debug(f"Fetching transcript for video ID: {video_id}")
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        logger.debug("Transcript fetched successfully.")
        return transcript
    except Exception as e:
        logger.error(f"Error fetching transcript: {e}")
        raise RuntimeError(f"Error fetching transcript: {e}")

def format_transcript(transcript):
    """
    Reformat the transcript into a readable format.
    """
    try:
        logger.debug("Formatting transcript.")
        formatted_text = ""
        for entry in transcript:
            formatted_text += f"{entry['text']}\n"
        logger.debug("Transcript formatted successfully.")
        return formatted_text
    except Exception as e:
        logger.error(f"Error formatting transcript: {e}")
        raise

def reformat_with_openai(transcript):
    """
    Use OpenAI API to reformat the transcript for readability in Google Docs.
    """
    try:
        logger.debug("Reformatting transcript with OpenAI API.")
        prompt = "Reformat the following YouTube transcript to make it readable for a Google Docs document. Keep the same exact words.\n" + transcript
        response = openai.Completion.create(
            model="gpt-3.5-turbo",
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7
        )
        reformatted_text = response.choices[0].text.strip()
        logger.debug("OpenAI API processing complete.")
        return reformatted_text
    except Exception as e:
        logger.error(f"Error reformating with OpenAI: {e}")
        try:
            # Fallback to using Ollama for reformatting
            logger.debug("Attempting to reformat with Ollama as a fallback.")
            prompt = "Reformat the following YouTube transcript to make it readable for a Google Docs document. Keep the same exact words.\n" + transcript
            ollama_command = ["ollama", "run", "llama3.1"]
            result = subprocess.run(ollama_command, input=prompt, capture_output=True, text=True)
            if result.returncode == 0:
                reformatted_text = result.stdout.strip()
                logger.debug("Ollama processing complete.")
                return reformatted_text
            else:
                raise RuntimeError(f"Ollama error: {result.stderr}")
        except Exception as ollama_error:
            logger.error(f"Error reformating with Ollama: {ollama_error}")
            raise RuntimeError(f"Error reformating with both OpenAI and Ollama: {e}, {ollama_error}")

@app.route('/', methods=['GET', 'POST'])
def index():
    transcript = ""
    reformatted_transcript = ""
    error_message = ""
    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url')
        try:
            logger.debug(f"Received YouTube URL: {youtube_url}")
            video_id = get_video_id(youtube_url)
            transcript_data = fetch_transcript(video_id)
            transcript = format_transcript(transcript_data)
            reformatted_transcript = reformat_with_openai(transcript)
        except ValueError as e:
            error_message = str(e)
            logger.error(f"ValueError: {error_message}")
        except RuntimeError as e:
            error_message = str(e)
            logger.error(f"RuntimeError: {error_message}")
    
    return render_template_string('''
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>YouTube Transcript Fetcher</title>
          </head>
          <body>
            <div style="text-align: center; margin-top: 50px;">
                <h1>YouTube Transcript Fetcher</h1>
                <form method="POST" action="/">
                    <input type="text" name="youtube_url" placeholder="Enter YouTube Video URL" style="width: 300px; padding: 5px;">
                    <button type="submit" style="padding: 5px 10px;">Get Transcript</button>
                </form>
                <div style="margin-top: 20px;">
                    {% if error_message %}
                        <p style="color: red;">{{ error_message }}</p>
                    {% endif %}
                    {% if reformatted_transcript %}
                        <h3>Reformatted Transcript:</h3>
                        <pre style="text-align: left; width: 60%; margin: 0 auto; padding: 10px; border: 1px solid #ccc; white-space: pre-wrap;">{{ reformatted_transcript }}</pre>
                    {% endif %}
                </div>
            </div>
          </body>
        </html>
    ''', transcript=transcript, reformatted_transcript=reformatted_transcript, error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)