from youtube_transcript_api import YouTubeTranscriptApi
import openai
from urllib.parse import urlparse, parse_qs
import requests
from requests.auth import HTTPBasicAuth
import os
import logging

logging.basicConfig(filename='app.log', filemode='a',
                    format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def get_video_id_from_url(url):
    """
    Extracts the YouTube video ID from a given URL.

    Supports both 'youtube.com' and 'youtu.be' URL formats. For 'youtube.com', it looks for the 'v' query parameter.
    For 'youtu.be', it extracts the ID directly from the path.

    Parameters:
        url (str): The full URL of the YouTube video.

    Returns:
        str: The extracted video ID if found, otherwise None.

    Note:
        This function silently handles exceptions and returns None if the video ID cannot be extracted.
    """
    try:
        url_data = urlparse(url)
        if url_data.hostname == 'www.youtube.com' or url_data.hostname == 'youtube.com':
            query = parse_qs(url_data.query)
            video_id = query.get("v")
            if video_id:
                logging.info(f"Video ID {video_id[0]} extracted from URL.")
                return video_id[0]
        elif url_data.hostname == 'youtu.be':
            # Extract the video ID from the path for youtu.be URLs
            video_id = url_data.path[1:]  # Remove the leading '/'
            if video_id:
                logging.info(f"Video ID {video_id} extracted from URL.")
                return video_id
        
        logging.warning(f"No video ID found in URL: {url}")
        return None
    except Exception as e:
        logging.error(f"Error extracting video ID from URL {url}: {e}")
        return None
    
def get_first_youtube_video_url(urls):
    """
    Finds and returns the first YouTube video URL from a list of URLs.

    Iterates over a provided list of URLs, checking each for a substring that matches
    'youtube' or 'youtu.be'. Returns the first URL that matches these criteria.

    Parameters:
        urls (list of str): A list containing URLs to be checked.

    Returns:
        str: The first YouTube video URL found in the list, or None if no YouTube URL is found.
    """
    for url in urls:
        if 'youtube' in url or 'youtu.be' in url:
            return url
    return None

def get_youtube_url(opportunity_id):
    """
    Retrieves the YouTube video URL associated with a given opportunity ID from the Lever API.

    This function makes a GET request to the Lever API to fetch the opportunity details using the provided
    opportunity ID. It then extracts and returns the first YouTube video URL found in the 'links' section
    of the opportunity data.

    Parameters:
        opportunity_id (str): The unique identifier for the opportunity in the Lever system.

    Returns:
        str: The YouTube video URL associated with the opportunity, or None if no YouTube URL is found.

    Note:
        Requires the 'LeverKey' environment variable to be set for authentication with the Lever API.
    """
    url = 'https://api.lever.co/v1/opportunities/{}'.format(opportunity_id)
    response = requests.get(url, auth=HTTPBasicAuth(os.getenv('LeverKey'),''))

    links = response.json()['data']['links']
    youtube_link = get_first_youtube_video_url(links)
    
    return youtube_link

def parse_decision_to_binary(decision_text):
    """
    Converts a decision text to a binary outcome based on the presence of the word 'yes'.

    This function checks if the word 'yes' is present in the provided decision text, performing
    a case-insensitive comparison. It is designed to interpret a textual decision as a binary
    outcome, where the presence of 'yes' indicates a positive (True) decision, and its absence
    indicates a negative (False) decision.

    Parameters:
        decision_text (str): The decision text to be analyzed.

    Returns:
        bool: True if 'yes' is present in the decision text, False otherwise.
    """
    decision_text_lower = decision_text.lower()
    return "yes" in decision_text_lower

def get_transcript_data_and_pause_count(video_id):
    """
    Fetches a video's transcript, calculates its total duration in minutes, and counts pauses between segments.

    Utilizes the YouTubeTranscriptApi to retrieve the English transcript of a video given its ID, then analyzes
    the transcript to determine the total duration and estimate the number of pauses based on gaps between
    transcript segments.

    Parameters:
        video_id (str): The unique identifier of the YouTube video.

    Returns:
        tuple: A tuple containing the full transcript text (str), total duration in minutes (int),
               and the estimated number of pauses (int), or (None, None, None) if an error occurs.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        if transcript:
            last_segment = transcript[-1]
            total_duration = last_segment['start'] + last_segment['duration']

            # Estimate the number of pauses
            pauses = 0
            for i in range(1, len(transcript)):
                current_start = transcript[i]['start']
                previous_end = transcript[i-1]['start'] + transcript[i-1]['duration']
                if current_start > previous_end:
                    pauses += 1

            full_transcript = " ".join(segment['text'] for segment in transcript)
            logging.info(f"Transcript retrieved successfully for video ID {video_id}.")
            return full_transcript, total_duration // 60, pauses
    except Exception as e:
        logging.error(f"Failed to retrieve transcript for video ID {video_id}. Error: {e}")
        return None, None, None

def analyze_transcript(url):
    """
    Analyzes a YouTube video's transcript for content quality, using a predefined prompt for GPT evaluation.

    This function reads a prompt from 'prompt.txt', extracts the video ID from the provided URL, retrieves the
    video's transcript and its analysis metrics (total duration and pauses), and evaluates these metrics against
    a GPT model to determine if the candidate qualifies for an interview.

    Parameters:
        url (str): The URL of the YouTube video to be analyzed.

    Returns:
        str: A message indicating whether the candidate qualifies for an interview, an error message if the
             video URL is invalid or the transcript could not be retrieved, or a detailed error message if
             any other error occurs during processing.
    """
    try:
        with open('prompt.txt', 'r') as file:
            prompt = file.read()
    except Exception as e:
        logging.error(f"Error opening or reading from 'prompt.txt': {e}")
        return "Error processing the prompt file."

    try:
        video_id = get_video_id_from_url(url)
        if not video_id:
            logging.error("Invalid URL provided.")
            return "Unable to process the video URL. Currently only YouTube URLs are accepted."

        full_transcript, total_duration, pauses = get_transcript_data_and_pause_count(
            video_id)

        if full_transcript is None:  # If there was an error retrieving the transcript
            logging.error("Error retrieving the transcript.")
            return pauses

        # Define the prompt for GPT evaluation based on the rubric
        prompt = prompt.format(full_transcript, pauses, total_duration)

        # Using the new OpenAI client structure
        client = openai.OpenAI(api_key=os.getenv('OpenAIKey'))
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
        )

        decision = parse_decision_to_binary(response.choices[0].message.content.strip())

        if decision:
            return "The candidate qualifies for an interview."
        return "The candidate does not qualify for an interview."
    except Exception as e:
        logging.error(f"An error occurred during the analysis: {e}")
        return f"An error occurred during the processing. {e}"
