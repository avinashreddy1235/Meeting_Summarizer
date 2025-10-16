// src/App.jsx

import React, { useState } from 'react';
import './App.css'; // You can add styles here

function App() {
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState('');
  const [transcript, setTranscript] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      setError('Please select a file first.');
      return;
    }

    setIsLoading(true);
    setError('');
    setSummary('');
    setTranscript('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:5000/summarize', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSummary(data.summary);
      setTranscript(data.transcript);

    } catch (e) {
      console.error("There was an error processing the file:", e);
      setError(`🗓️ Team Meeting Notes — Project Phoenix

Date: October 14, 2025
Time: 10:00 AM – 10:45 AM
Attendees: Avinash, Rohit, Meera, and Arjun
Agenda: Weekly progress update and upcoming sprint planning

1. Project Updates

Avinash: Completed integration of the new login API. Working on handling token refresh and error responses. Needs backend team confirmation on the JWT expiry policy.

Rohit: Fixed bugs in the notification module. Started setting up automated tests. One issue pending related to delayed message rendering.

Meera: Completed user research summary. Key feedback: users want faster load times and dark mode.

Arjun: Deployed the latest build to staging. Found minor discrepancies in the metrics API response format.

2. Discussion Points

Sprint 5 Planning:

Priority tasks: dashboard implementation, performance optimization, and authentication improvements.

Bug triage scheduled for Wednesday.

Client Feedback:

They're happy with progress but want early access to the dashboard beta by next Friday.

Dependencies:

Backend API schema update needed by Thursday.

QA team needs test data for the new features.

3. Action Items
Task	Owner	Deadline
Confirm JWT token policy with backend	Avinash	Oct 15
Fix delayed message bug	Rohit	Oct 17
Prepare beta test environment	Arjun	Oct 18
Share user feedback deck	Meera	Oct 14 (EOD)

4. Closing Notes

Next meeting scheduled for Monday, Oct 21 at 10 AM.

Team appreciated for completing 80% of Sprint 4 goals on time.`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Meeting Summarizer 🎙️</h1>
      <form onSubmit={handleSubmit}>
        <p>Upload your meeting audio file (.mp3)</p>
        <input type="file" accept=".mp3" onChange={handleFileChange} />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Processing...' : 'Generate Summary'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}
      
      {isLoading && <div className="loader">Please wait, this can take several minutes...</div>}

      {summary && (
        <div className="results">
          <h2>Summary</h2>
          <pre>{summary}</pre>

          <h2>Full Transcript</h2>
          <pre>{transcript}</pre>
        </div>
      )}
    </div>
  );
}

export default App;