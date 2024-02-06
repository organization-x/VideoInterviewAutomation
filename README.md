---
title: VideoInterviewAutomation
emoji: 🚀
colorFrom: yellow
colorTo: red
sdk: gradio
sdk_version: 4.16.0
app_file: app.py
pinned: false
license: mit
---

# YouTube Interview Analysis Tool

This application evaluates YouTube video interviews to recommend whether the interviewee should be considered for a further interview based on a specific rubric. It leverages the YouTube Transcript API to fetch transcripts, analyzes the content with OpenAI's GPT-4, and provides recommendations through a simple web interface powered by Gradio.

## Features

- **Video ID Extraction**: Extracts the video ID from a YouTube URL.
- **Transcript Retrieval**: Retrieves the video's transcript along with its total duration and an estimated number of pauses.
- **GPT-4 Analysis**: Analyzes the transcript data against a predefined rubric to assess the interviewee's performance.
- **Gradio Interface**: Offers a user-friendly web interface for inputting YouTube URLs and receiving recommendations.