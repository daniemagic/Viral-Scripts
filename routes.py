# routes.py

from flask import Blueprint, request, render_template
import logging
import subprocess
from utils import (
    get_video_id,
    fetch_video_title,
    fetch_transcript,
    format_transcript,
    reformat_with_ollama,
    reformat_with_openai,
)
import os
from dotenv import load_dotenv

# Initialize Blueprint
app = Blueprint('app', __name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get YouTube API key
youtube_api_key = os.getenv('YOUTUBE_API_KEY')

if not youtube_api_key:
    raise ValueError("YouTube API key not found. Please set YOUTUBE_API_KEY in your .env file.")

# Define your routes here
@app.route('/', methods=['GET', 'POST'])
def index():
    original_transcript = ""
    reformatted_transcript = ""
    rehashed_transcript = ""
    error_message = ""

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'fetch_transcript':
            youtube_url = request.form.get('youtube_url')
            try:
                logger.debug(f"Received YouTube URL: {youtube_url}")
                video_id = get_video_id(youtube_url)
                video_title = fetch_video_title(video_id)
                transcript_data = fetch_transcript(video_id)
                original_transcript = format_transcript(transcript_data)
                try:
                    reformatted_transcript = reformat_with_ollama(original_transcript, video_title)
                except RuntimeError:
                    logger.debug("Ollama failed, falling back to OpenAI API.")
                    reformatted_transcript = reformat_with_openai(original_transcript, video_title)
            except ValueError as e:
                error_message = str(e)
                logger.error(f"ValueError: {error_message}")
            except RuntimeError as e:
                error_message = str(e)
                logger.error(f"RuntimeError: {error_message}")

        elif action == 'rehash':
            # Rehash without niche
            reformatted_transcript = request.form.get('reformatted_transcript')
            if reformatted_transcript:
                try:
                    logger.debug("Rehashing transcript without niche using Ollama.")
                    prompt = (
                        f"Rehash the following YouTube transcript for the same topic. "
                        "In other words, keep the same hook and script sentence structure but word the subject matter slightly differently.\n\n"
                        + reformatted_transcript
                    )
                    rehashed_transcript = reformat_with_ollama(reformatted_transcript, "")
                except RuntimeError:
                    logger.debug("Ollama failed, falling back to OpenAI API.")
                    try:
                        rehashed_transcript = reformat_with_openai(reformatted_transcript, "")
                    except RuntimeError as e:
                        error_message = str(e)
                        logger.error(f"RuntimeError: {error_message}")
            else:
                error_message = "Reformatted transcript not found."

        elif action == 'rehash_niche':
            # Rehash with niche
            reformatted_transcript = request.form.get('reformatted_transcript')
            niche_description = request.form.get('niche_description')
            if reformatted_transcript and niche_description:
                try:
                    logger.debug(f"Rehashing transcript with niche: {niche_description} using Ollama.")
                    prompt = (
                        f"Rehash the following YouTube transcript but make the subject matter about {niche_description}. " +
                        "In other words, keep the same hook and script sentence structure but make the subject matter about {niche_description}.\n\n"  + reformatted_transcript
                        
                    )
                    rehashed_transcript = reformat_with_ollama(reformatted_transcript, niche_description, niche_description)
                except RuntimeError:
                    logger.debug("Ollama failed, falling back to OpenAI API.")
                    try:
                        rehashed_transcript = reformat_with_openai(reformatted_transcript, niche_description)
                    except RuntimeError as e:
                        error_message = str(e)
                        logger.error(f"RuntimeError: {error_message}")
            else:
                error_message = "Reformatted transcript or niche description not provided."

    return render_template(
        'index.html',
        original_transcript=original_transcript,
        reformatted_transcript=reformatted_transcript,
        rehashed_transcript=rehashed_transcript,
        error_message=error_message
    )
