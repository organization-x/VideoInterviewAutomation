# README for YouTube Video Analysis and Lever Integration

## Overview

This Python application is designed to analyze YouTube video transcripts to evaluate content quality and integrate with Lever, a popular Applicant Tracking System (ATS), to automate the recruitment process. It extracts YouTube video IDs from URLs, retrieves video transcripts, analyzes the content using OpenAI's GPT model, and posts the analysis results to Lever. The application is structured to handle webhooks for processing video interviews associated with specific opportunities in Lever.

## Features

- **YouTube Video ID Extraction**: Supports both 'youtube.com' and 'youtu.be' formats to extract video IDs.
- **Transcript Retrieval and Analysis**: Utilizes the `YouTubeTranscriptApi` to fetch video transcripts and calculates total duration and pause counts to estimate content quality.
- **OpenAI GPT Analysis**: Analyzes the transcript content using a predefined prompt and OpenAI's GPT model to make a decision on the candidate's qualification.
- **Lever Integration**: Posts the analysis results to Lever by adding a note to the candidate's opportunity record.
- **Error Handling and Logging**: Implements comprehensive error handling and logging for troubleshooting and audit trails.

## Requirements

- Python 3.x
- Flask
- Requests
- `youtube_transcript_api` Python package
- `openai` Python package

## Setup and Configuration

1. **Environment Variables**: Set the following environment variables:
   - `LeverKey`: Your Lever API key for authentication.
   - `OpenAIKey`: Your OpenAI API key for accessing GPT models.

2. **Dependencies**: Install the required Python packages by running:

`pip install -r requirements.txt`

3. **Logging**: The application logs its operations in `app.log`. Ensure the log file is writable.

## Usage

1. **Start the Flask Application**: Run the application with Flask by executing:

`python app.py`

2. **Webhook Configuration**: Configure a webhook in Lever to POST to the `/webhook` endpoint of this application whenever a relevant event occurs.

3. **Analysis and Integration**: When the application receives a webhook event, it processes the video URL from the opportunity, analyzes the transcript, and posts the result back to Lever.

## API Endpoints

- `/webhook`: Accepts POST requests to process incoming webhooks from Lever, analyze video transcripts, and update Lever opportunities with the analysis results.

## Error Handling

The application includes error handling for various scenarios, including invalid URLs, failure to retrieve transcripts, and issues with Lever or OpenAI API requests. Errors are logged to `app.log` for review.

## Security Considerations

Ensure that your Lever and OpenAI API keys are securely stored and not exposed in the code or logs. Use environment variables to manage these keys securely.
