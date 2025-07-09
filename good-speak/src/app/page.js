// src/app/page.js
'use client';
import { useState } from 'react';

export default function Home() {
  const [username, setUsername] = useState('test_user');
  const [message, setMessage] = useState('You are an idiot');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch('/api/moderate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, message }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({ error: String(err) });
    }
    setLoading(false);
  };

  return (
    <main style={{ fontFamily: 'Arial, sans-serif', margin: '2em', color: '#333' }}>
      <h1>Good Speak API</h1>
      <p>Translate potentially harmful messages into polite alternatives.</p>
      <section>
        <h2>Try It Live</h2>
        <form onSubmit={handleSubmit} style={{ border: '1px solid #ddd', padding: '1em', borderRadius: '4px' }}>
          <label>
            Username (API Key):
            <input value={username} onChange={e => setUsername(e.target.value)} style={{ width: '100%', padding: '0.5em', marginTop: '0.2em' }} />
          </label>
          <label>
            Message to moderate:
            <textarea rows={3} value={message} onChange={e => setMessage(e.target.value)} style={{ width: '100%', padding: '0.5em', marginTop: '0.2em' }} />
          </label>
          <button type="submit" disabled={loading} style={{ marginTop: '1em', padding: '0.5em 1em' }}>{loading ? 'Processing...' : 'Submit'}</button>
        </form>
        <div style={{ marginTop: '1em', whiteSpace: 'pre-wrap' }}>
          {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
        </div>
      </section>
      <section style={{ marginTop: '2em' }}>
        <h2>Endpoint</h2>
        <p><code>POST /api/moderate</code></p>
        <h2>Request Fields</h2>
        <ul>
          <li><code>username</code>: Your API key or identifier</li>
          <li><code>message</code>: The text you want checked</li>
        </ul>
        <h2>Response</h2>
        <pre>{`{
  "flagged": true|false,
  "toxicity": 0.0-1.0,
  "suggestion": "Rewritten message" | null
}`}</pre>
        <h2>Example CURL</h2>
        <pre>{`curl -X POST http://localhost:3000/api/moderate \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "message": "Hey, could you please be less noisy?"
}'`}</pre>
        <h2>Rate Limiting</h2>
        <p>Clients are limited to <strong>100 requests per hour</strong>. Exceeding this will return <code>429 Too Many Requests</code>.</p>
      </section>
    </main>
  );
}
