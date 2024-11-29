# utils.py

import re
import logging
import requests
import subprocess
import openai
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
import os

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Get YouTube API key
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

def reformat_with_ollama(transcript, title, niche = "none"):
    """
    Use Ollama to reformat the transcript for readability in Google Docs.
    """
    try:
        logger.debug("Reformatting transcript with Ollama.")
        if title:
            prompt = (
                f"Title: {title}\n\n"
                "Reformat the following YouTube transcript to make it readable for a Google Docs document. "
                "Keep the same exact words.\n"
                "Format the output with 'Caption: <title>' followed by the transcript text.\n" 
                + transcript
            )
        elif (niche == "none"):
            prompt = (
                "Rehash the following YouTube transcript for the same topic. "
                "In other words, keep the same hook and script sentence structure but word the subject matter slightly differently.\n\n"
                + transcript
            )
        else:
            prompt = (
                    "Rehash the following YouTube transcript but make the subject matter about {niche}." +
                        "In other words, keep the same hook and script sentence structure but make the subject matter about {niche}.\n\n"  + transcript
                        
                    )
        ollama_command = ["ollama", "run", "llama3.1"]
        result = subprocess.run(ollama_command, input=prompt, capture_output=True, text=True)
        if result.returncode == 0:
            reformatted_text = result.stdout.strip()
            logger.debug("Ollama processing complete.")
            return reformatted_text
        else:
            raise RuntimeError(f"Ollama error: {result.stderr}")
    except Exception as e:
        logger.error(f"Error reformatting with Ollama: {e}")
        raise

def reformat_with_openai(transcript, title):
    """
    Use OpenAI API to reformat the transcript for readability in Google Docs.
    """
    try:
        logger.debug("Reformatting transcript with OpenAI API.")
        if title:
            prompt = (
                f"Title: {title}\n\n"
                "Reformat the following YouTube transcript to make it readable for a Google Docs document. "
                "Keep the same exact words.\n"
                "Format the output with 'Caption: <title>' followed by the transcript text.\n" 
                + transcript
            )
        else:
            prompt = (
                "Rehash the following YouTube transcript for the same topic. "
                "Keep the same hook and structure but word things slightly differently.\n\n"
                + transcript
            )
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
        logger.error(f"Error reformatting with OpenAI: {e}")
        raise
