import pytest
from app import app, db, Meeting
import os
import io

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

def test_summarize_endpoint_no_file(client):
    response = client.post('/summarize')
    assert response.status_code == 400
    assert b'No file provided' in response.data

def test_summarize_endpoint_empty_file(client):
    data = {'file': (io.BytesIO(b''), '')}
    response = client.post('/summarize', data=data)
    assert response.status_code == 400
    assert b'No file selected' in response.data

def test_summarize_endpoint_wrong_format(client):
    data = {'file': (io.BytesIO(b'test'), 'test.txt')}
    response = client.post('/summarize', data=data)
    assert response.status_code == 400
    assert b'Only MP3 files are supported' in response.data

def test_database_storage(client):
    # Create a test meeting
    meeting = Meeting(
        filename='test.mp3',
        transcript='Test transcript',
        summary='Test summary'
    )
    with app.app_context():
        db.session.add(meeting)
        db.session.commit()
        
        # Query the meeting
        stored_meeting = Meeting.query.first()
        assert stored_meeting.filename == 'test.mp3'
        assert stored_meeting.transcript == 'Test transcript'
        assert stored_meeting.summary == 'Test summary'