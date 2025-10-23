from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
import openai
from werkzeug.utils import secure_filename
import tempfile

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///meetings.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Models
class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    transcript = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    action_items = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()

def transcribe_audio(audio_file_path):
    """Transcribe audio using OpenAI Whisper API"""
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            return transcript.text
    except Exception as e:
        print(f"Transcription error: {str(e)}")
        raise

def generate_summary_and_actions(transcript):
    """Generate meeting summary and action items using OpenAI GPT"""
    try:
        prompt = f"""Please analyze this meeting transcript and provide the following in a structured format:

1. SUMMARY:
   A concise summary highlighting key decisions and main discussion points

2. ACTION_ITEMS:
   A list of specific action items, each on a new line starting with '- '
   Include assignee (if mentioned) and deadline (if mentioned)

Transcript:
{transcript}

Please format your response exactly as:
SUMMARY:
(your summary here)

ACTION_ITEMS:
(your action items here, one per line)"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a meeting assistant that creates clear, structured summaries and extracts action items. Always use the exact format specified."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        # Parse the response
        parts = content.split("ACTION_ITEMS:")
        if len(parts) != 2:
            raise ValueError("Unexpected response format from GPT")
            
        summary_part = parts[0].replace("SUMMARY:", "").strip()
        action_items = parts[1].strip()
        
        return summary_part, action_items
    except Exception as e:
        print(f"Summary generation error: {str(e)}")
        raise

@app.route('/summarize', methods=['POST'])
def summarize_meeting():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.mp3'):
        return jsonify({'error': 'Only MP3 files are supported'}), 400

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            file.save(temp_file.name)
            
            # Transcribe audio
            transcript = transcribe_audio(temp_file.name)
            
            # Generate summary and action items
            response = generate_summary_and_actions(transcript)
            content = response.choices[0].message.content
            
            # Parse the response
            parts = content.split("ACTION_ITEMS:")
            if len(parts) != 2:
                raise ValueError("Unexpected response format from GPT")
                
            summary = parts[0].replace("SUMMARY:", "").strip()
            action_items = parts[1].strip()
            
            # Store in database
            meeting = Meeting(
                filename=secure_filename(file.filename),
                transcript=transcript,
                summary=summary,
                action_items=action_items
            )
            db.session.add(meeting)
            db.session.commit()
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
            return jsonify({
                'transcript': transcript,
                'summary': summary,
                'action_items': action_items,
                'meeting_id': meeting.id
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)