import pytest
from app import app, db, Meeting, transcribe_audio, generate_summary_and_actions
import os
import io
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def mock_openai():
    with patch('openai.ChatCompletion.create') as mock_chat, \
         patch('openai.Audio.transcribe') as mock_transcribe:
        
        # Mock transcription response
        mock_transcribe.return_value = MagicMock(text="This is a test transcript.")
        
        # Mock GPT response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """SUMMARY:
Test meeting summary discussing key points.

ACTION_ITEMS:
- John to complete the report by Friday
- Sarah to review documentation
- Team to schedule follow-up meeting"""
        mock_chat.return_value = mock_response
        
        yield (mock_chat, mock_transcribe)

def test_transcribe_audio(mock_openai):
    with open("test_audio.mp3", "wb") as f:
        f.write(b"test audio content")
    
    transcript = transcribe_audio("test_audio.mp3")
    assert transcript == "This is a test transcript."
    os.remove("test_audio.mp3")

def test_generate_summary_and_actions(mock_openai):
    transcript = "This is a test transcript"
    summary, action_items = generate_summary_and_actions(transcript)
    
    assert "Test meeting summary" in summary
    assert "John to complete" in action_items
    assert "Sarah to review" in action_items

def test_full_processing_flow(client, mock_openai):
    mock_chat, mock_transcribe = mock_openai
    
    # Mock the response specifically for this test
    mock_transcribe.return_value = MagicMock(text="This is a test transcript.")
    mock_chat.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="""SUMMARY:
Test meeting summary discussing key points.

ACTION_ITEMS:
- John to complete the report by Friday
- Sarah to review documentation
- Team to schedule follow-up meeting"""
                )
            )
        ]
    )
    
    # Create test audio file
    test_audio = io.BytesIO(b"test audio content")

    # Submit file to endpoint
    data = {'file': (test_audio, 'meeting.mp3')}
    response = client.post('/summarize', data=data)

    # Check response
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'transcript' in json_data
    assert 'summary' in json_data
    assert 'action_items' in json_data
    assert 'meeting_id' in json_data
    
    # Verify database storage
    with app.app_context():
        meeting = Meeting.query.get(json_data['meeting_id'])
        assert meeting is not None
        assert meeting.transcript == "This is a test transcript."
        assert "Test meeting summary" in meeting.summary
        assert "John to complete" in meeting.action_items

def test_error_handling(client, mock_openai):
    mock_chat, mock_transcribe = mock_openai
    # Mock API error
    mock_transcribe.side_effect = Exception("API Error")
    
    # Submit file
    test_audio = io.BytesIO(b"test audio content")
    data = {'file': (test_audio, 'meeting.mp3')}
    
    # Check error response
    response = client.post('/summarize', data=data)
    assert response.status_code == 500
    assert 'error' in response.get_json()

def test_transcription_quality():
    """
    This is a placeholder for a more comprehensive test that would:
    1. Use a known audio file with ground truth transcript
    2. Compare transcription output with expected text
    3. Calculate WER (Word Error Rate) or similar metrics
    """
    pass

def test_summary_quality():
    """
    This is a placeholder for a more comprehensive test that would:
    1. Use a known transcript with ground truth summary
    2. Compare generated summary with expected output
    3. Use metrics like ROUGE or human evaluation
    """
    pass