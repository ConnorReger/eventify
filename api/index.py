from flask import Flask, request, jsonify
import google.generativeai as genai
import os
from google.cloud import speech_v1 as speech
import io

app = Flask(__name__)
# please insert api key
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key="AIzaSyDcrVklvjN4wd6nFuRlu3FQLwDQwKYSdRk")

@app.route("/api/python", methods=["POST"])
def image_to_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Read the file into memory
    image_content = file.read()
    
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    
    # Use the in-memory image content
    image_parts = [
        {
            "mime_type": file.content_type,
            "data": image_content
        }
    ]
    
    prompt = "Find and transcribe relevant event information. If an event cannot be found, return 'none'. If there are multiple events, put each on a new line."
    
    response = model.generate_content(image_parts + [prompt])
    
    toics = model.generate_content(
        [response.text, "\n\n", "Turn this event into an ICS file. Respond in text so that I can save the response as a .ics"]
    )
    
    ics_content = toics.text
    return jsonify({"ics_content": ics_content})

def voice_to_text():
    audio_file = request.files['audio']
    # Note the expected file is in mp3 format
    audio_path = os.path.join("api/uploads", "recording.mp3")
    audio_file.save(audio_path)

    # Initialize Google Cloud Speech client
    client = speech.SpeechClient()

    # Load the audio file for Google Cloud Speech API
    with open(audio_path, 'rb') as audio:
        content = audio.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=16000,  # Change this if your audio has a different sample rate
        language_code='en-US'  # Specify the language code
    )

    # Perform speech recognition
    response = client.recognize(config=config, audio=audio)

    # Extract the transcribed text from the response
    transcribed_text = ''
    for result in response.results:
        transcribed_text += result.alternatives[0].transcript

    # Use Generative AI to extract event information
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    toics = model.generate_content(
        [transcribed_text, "\n\n", "Turn this event into an ICS file. Respond in text so that I can save the response as a .ics"]
    )
    
    # Extract the text content for the ICS file
    ics_content = toics.text  
    # Define the file path where you want to save the .ics file
    ics_file_path = "event.ics"
    # Save the ICS content to a file
    with open(ics_file_path, "w") as ics_file:
        ics_file.write(ics_content)

    return ics_content