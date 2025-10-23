// src/App.jsx

import React, { useState } from 'react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState('');
  const [transcript, setTranscript] = useState('');
  const [actionItems, setActionItems] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState('');

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
      
      // Parse action items into array
      const items = data.action_items.split('\n')
        .map(item => item.trim())
        .filter(item => item.startsWith('-'))
        .map(item => item.substring(1).trim());
      setActionItems(items);

    } catch (e) {
      console.error("There was an error processing the file:", e);
      setError("Error processing the file. Please ensure the backend server is running and try again.");
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
      
      {isLoading && (
        <div className="loader">
          <p>Please wait, this can take several minutes...</p>
          <p>{progress}</p>
        </div>
      )}

      {summary && (
        <div className="results">
          <h2>Meeting Summary</h2>
          <pre>{summary}</pre>

          {actionItems && actionItems.length > 0 && (
            <>
              <h2>Action Items</h2>
              <ul className="action-items">
                {actionItems.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </>
          )}

          <h2>Full Transcript</h2>
          <pre>{transcript}</pre>
        </div>
      )}
    </div>
  );
}

export default App;