import re
import logging
import openai
from flask import Flask, request, render_template_string
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
import os
import subprocess
import requests

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get your OpenAI API key from the .env file
openai.api_key = os.getenv('OPENAI_API_KEY')
# Get your YouTube API key from the .env file
youtube_api_key = os.getenv('YOUTUBE_API_KEY')

if not youtube_api_key:
    raise ValueError("YouTube API key not found. Please set YOUTUBE_API_KEY in your .env file.")

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

def fetch_video_title(video_id):
    """
    Fetch the title of the YouTube video using YouTube API.
    """
    try:
        logger.debug(f"Fetching title for video ID: {video_id}")
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={youtube_api_key}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            title = data["items"][0]["snippet"]["title"]
            logger.debug(f"Video title fetched: {title}")
            return title
        else:
            raise RuntimeError("Unable to fetch video title.")
    except Exception as e:
        logger.error(f"Error fetching video title: {e}")
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

def reformat_with_ollama(transcript, title):
    """
    Use Ollama to reformat the transcript for readability in Google Docs.
    """
    try:
        logger.debug("Reformatting transcript with Ollama.")
        prompt = f"Title: {title}\n\nReformat the following YouTube transcript to make it readable for a Google Docs document. Keep the same exact words.\nFormat the output with 'Caption: <title>' followed by the transcript text.\n" + transcript
        ollama_command = ["ollama", "run", "llama3.1"]
        result = subprocess.run(ollama_command, input=prompt, capture_output=True, text=True)
        if result.returncode == 0:
            reformatted_text = result.stdout.strip()
            logger.debug("Ollama processing complete.")
            return reformatted_text
        else:
            raise RuntimeError(f"Ollama error: {result.stderr}")
    except Exception as e:
        logger.error(f"Error reformating with Ollama: {e}")
        raise

def reformat_with_openai(transcript, title):
    """
    Use OpenAI API to reformat the transcript for readability in Google Docs.
    """
    try:
        logger.debug("Reformatting transcript with OpenAI API.")
        prompt = f"Title: {title}\n\nReformat the following YouTube transcript to make it readable for a Google Docs document. Keep the same exact words.\nFormat the output with 'Caption: <title>' followed by the transcript text.\n" + transcript
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
        raise

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
            video_title = fetch_video_title(video_id)
            transcript_data = fetch_transcript(video_id)
            transcript = format_transcript(transcript_data)
            try:
                reformatted_transcript = reformat_with_ollama(transcript, video_title)
            except RuntimeError:
                logger.debug("Ollama failed, falling back to OpenAI API.")
                reformatted_transcript = reformat_with_openai(transcript, video_title)
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
            <title>Viral Scripts</title>
          </head>
          <body>
            <div style="text-align: center; margin-top: 50px;">
                <h1>Viral Scripts</h1>
                <p>Enter any YouTube Short link to get the transcript of viral shorts, easily store and edit like Google Docs, and click a button to rehash them for more content or tailor them to another niche.</p>
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
                        <form method="POST" action="/rehash">
                            <input type="hidden" name="transcript" value="{{ reformatted_transcript }}">
                            <button type="submit" style="padding: 5px 10px; margin-top: 10px;">Rehash</button>
                        </form>
                        <form method="POST" action="/rehash_niche" style="margin-top: 10px;">
                            <input type="hidden" name="transcript" value="{{ reformatted_transcript }}">
                            <input type="text" name="niche_description" placeholder="Enter new niche/topic" style="width: 300px; padding: 5px;">
                            <button type="submit" style="padding: 5px 10px;">Rehash for Different Niche</button>
                        </form>
                    {% endif %}
                </div>
            </div>
          </body>
        </html>
    ''', transcript=transcript, reformatted_transcript=reformatted_transcript, error_message=error_message)

@app.route('/rehash', methods=['POST'])
def rehash():
    transcript = request.form.get('transcript')
    try:
        logger.debug("Rehashing transcript with Ollama.")
        prompt = f"Rehash the following YouTube transcript for the same topic, but worded differently while keeping the hook and structure of the video:\n\n{transcript}"
        ollama_command = ["ollama", "run", "llama3.1"]
        result = subprocess.run(ollama_command, input=prompt, capture_output=True, text=True)
        if result.returncode == 0:
            reformatted_transcript = result.stdout.strip()
            logger.debug("Ollama rehash complete.")
            return render_template_string('''
                <!doctype html>
                <html lang="en">
                  <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                    <title>Viral Scripts - Rehashed</title>
                  </head>
                  <body>
                    <div style="text-align: center; margin-top: 50px;">
                        <h1>Rehashed Transcript</h1>
                        <pre style="text-align: left; width: 60%; margin: 0 auto; padding: 10px; border: 1px solid #ccc; white-space: pre-wrap;">{{ reformatted_transcript }}</pre>
                    </div>
                  </body>
                </html>
            ''', reformatted_transcript=reformatted_transcript)
        else:
            raise RuntimeError(f"Ollama error: {result.stderr}")
    except Exception as e:
        error_message = f"Error rehashing transcript: {e}"
        logger.error(error_message)
        return render_template_string('''
            <!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                <title>Viral Scripts - Error</title>
              </head>
              <body>
                <div style="text-align: center; margin-top: 50px;">
                    <p style="color: red;">{{ error_message }}</p>
                </div>
              </body>
            </html>
        ''', error_message=error_message)

@app.route('/rehash_niche', methods=['POST'])
def rehash_niche():
    transcript = request.form.get('transcript')
    niche_description = request.form.get('niche_description')
    try:
        logger.debug("Rehashing transcript for a different niche with Ollama.")
        prompt = f"Rehash the following YouTube transcript to fit the niche: {niche_description}. Keep the hook and structure of the video, but change the content to fit the new niche:\n\n{transcript}"
        ollama_command = ["ollama", "run", "llama3.1"]
        result = subprocess.run(ollama_command, input=prompt, capture_output=True, text=True)
        if result.returncode == 0:
            reformatted_transcript = result.stdout.strip()
            logger.debug("Ollama rehash for niche complete.")
            return render_template_string('''
                <!doctype html>
                <html lang="en">
                  <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                    <title>Viral Scripts - Rehashed for Different Niche</title>
                  </head>
                  <body>
                    <div style="text-align: center; margin-top: 50px;">
                        <h1>Rehashed Transcript for Different Niche</h1>
                        <pre style="text-align: left; width: 60%; margin: 0 auto; padding: 10px; border: 1px solid #ccc; white-space: pre-wrap;">{{ reformatted_transcript }}</pre>
                    </div>
                  </body>
                </html>
            ''', reformatted_transcript=reformatted_transcript)
        else:
            raise RuntimeError(f"Ollama error: {result.stderr}")
    except Exception as e:
        error_message = f"Error rehashing transcript for different niche: {e}"
        logger.error(error_message)
        return render_template_string('''
            <!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                <title>Viral Scripts - Error</title>
              </head>
              <body>
                <div style="text-align: center; margin-top: 50px;">
                    <p style="color: red;">{{ error_message }}</p>
                </div>
              </body>
            </html>
        ''', error_message=error_message)


if __name__ == '__main__':
    app.run(debug=True)