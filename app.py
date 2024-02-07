from flask import Flask, request, jsonify, make_response
from requests.auth import HTTPBasicAuth
from helpers import *
import requests
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def post_candidate_analysis_to_lever(analysis_result, candidate_id):
    """
    Sends the analysis result of a candidate's video interview to Lever via a POST request.

    This function constructs a request to the Lever API to add a note to a specific opportunity
    (candidate) identified by the candidate_id. The note contains the result of the machine learning
    analysis of the candidate's video interview. It handles various exceptions that might occur during
    the request, logs the attempt and outcome of the request, and ensures that any HTTP or connection
    errors are caught and logged appropriately.

    Parameters:
    - analysis_result (str): The result of the video interview analysis to be sent to Lever.
    - candidate_id (str): The unique identifier for the candidate/opportunity in Lever.

    Returns:
    - dict: The JSON response from the Lever API if the request is successful.
    - None: If the request fails due to an exception, the function returns None.

    The function logs an info message before sending the data, and upon successful data transmission.
    In case of exceptions such as HTTPError, ConnectionError, Timeout, or any other RequestException,
    it logs the specific error. A general exception catch is also implemented to log any unexpected errors.

    It uses the requests library for making HTTP requests, and the HTTPBasicAuth for authentication.
    The Lever API key is expected to be available as an environment variable 'LeverKey'.
    """
    lever_api_url = 'https://api.lever.co/v1/opportunities/{}/notes'.format(candidate_id)
    data = {
        "value": "Video Interview ML Decision: {}".format(analysis_result)
    }
    
    try:
        # Log the attempt to send data
        logging.info(f"Sending analysis result to Lever for candidate ID {candidate_id}")
        
        response = requests.post(lever_api_url, auth=HTTPBasicAuth(os.getenv('LeverKey'), ''), json=data)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Log successful data sending
        logging.info(f"Successfully sent analysis result to Lever for candidate ID {candidate_id}")
        
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        # Log HTTP errors (e.g., 404, 401, etc.)
        logging.error(f'HTTP error occurred: {http_err}')
    except requests.exceptions.ConnectionError as conn_err:
        # Log connection errors (e.g., DNS failure, refused connection, etc.)
        logging.error(f'Connection error occurred: {conn_err}')
    except requests.exceptions.Timeout as timeout_err:
        # Log timeout errors
        logging.error(f'Timeout error occurred: {timeout_err}')
    except requests.exceptions.RequestException as req_err:
        # Log any other requests-related errors
        logging.error(f'Error sending data to Lever: {req_err}')
    except Exception as e:
        # Catch-all for any other exceptions not related to requests
        logging.error(f'An unexpected error occurred: {e}')

    # Return None or an appropriate response in case of failure
    return None

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """
    Processes incoming webhook POST requests, analyzes video transcripts, and posts results to Lever.

    Validates the presence of required data ('opportunityId') in the request, retrieves the candidate's
    video URL, analyzes the video transcript, and sends the analysis result to Lever. It handles errors
    at each step by logging the error and returning an appropriate HTTP response.

    Returns:
        - A success response with the analysis result and a 200 status code if all operations succeed.
        - An error response with a relevant message and an appropriate status code (400, 404, 500) if any operation fails.
    """
    try:
        data = request.json
        if not data:
            # If no data is received
            logging.error("No data received in request")
            return make_response(jsonify({"error": "No data received"}), 400)

        data = data['data']
        if data.get('toStageId') != os.getenv('VideoStageId'):
            logging.error("Invalid credentials submitted in request.")
            return make_response(jsonify({"error": "Invalid credentials submitted."}), 403)
        
        opportunity_id = data.get('opportunityId')
        if not opportunity_id:
            # If opportunityId is not provided in the data
            logging.error("No opportunityId provided")
            return make_response(jsonify({"error": "No opportunityId provided"}), 400)

        candidate_video_url = get_youtube_url(opportunity_id)
        if not candidate_video_url:
            # If no URL is returned for the given opportunity_id
            logging.error(f"Unable to process video URL for opportunityId {opportunity_id}")
            analysis_result = "Unable to process the video URL. Currently only YouTube URLs are accepted."

            return jsonify(analysis_result), 200

        analysis_result = analyze_transcript(candidate_video_url)
        if analysis_result is None:
            # Handle case where analysis_result is None or an error occurred during analysis
            logging.error(f"Error analyzing transcript for opportunityId {opportunity_id}")
            return make_response(jsonify({"error": "Failed to analyze transcript"}), 500)

        send_result = post_candidate_analysis_to_lever(analysis_result, opportunity_id)
        if send_result is None:
            # Assuming post_candidate_analysis_to_lever returns None on failure
            logging.error(f"Failed to send results to Lever for opportunityId {opportunity_id}")
            return make_response(jsonify({"error": "Failed to send results to Lever"}), 500)
        print('done')
        return jsonify(analysis_result), 200
    except Exception as e:
        print(e)
        logging.error(f"An unexpected error occurred: {e}")
        return make_response(jsonify({"error": "An unexpected error occurred"}), 500)

if __name__ == '__main__':
    app.run(debug=True,port=5002)
