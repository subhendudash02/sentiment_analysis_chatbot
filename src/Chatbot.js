import React, { useState, useRef, useEffect } from 'react';

function Chatbot({ apiUrl = 'http://127.0.0.1:8000/sentiment-analysis' }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello! How can I assist you today?' }
  ]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const chatEndRef = useRef(null);

  // Initialize or retrieve session ID when component mounts
  useEffect(() => {
    let existingSessionId = localStorage.getItem('chatSessionId');
    if (!existingSessionId) {
      existingSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('chatSessionId', existingSessionId);
    }
    setSessionId(existingSessionId);
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, open]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMessage = { sender: 'user', text: input, sessionId };
    setMessages((msgs) => [...msgs, userMessage]);
    setInput('');
    setLoading(true);
    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.text,
          session_id: sessionId
        })
      });
      if (response.ok) {
        const data = await response.json();
        setMessages((msgs) => [
          ...msgs,
          { sender: 'bot', text: data.response || 'No response from AI.', sessionId }
        ]);
      } else {
        setMessages((msgs) => [
          ...msgs,
          { sender: 'bot', text: 'AI service error. Please try again.' }
        ]);
      }
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        { sender: 'bot', text: 'Network error. Please try again.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating button */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          style={{
            position: 'fixed',
            bottom: 32,
            right: 32,
            zIndex: 1000,
            background: '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: '50%',
            width: 64,
            height: 64,
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            fontSize: 32,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 0.2s',
          }}
          aria-label="Open chatbot"
        >
          <span role="img" aria-label="chat">💬</span>
        </button>
      )}
      {/* Chatbot window */}
      {open && (
        <div
          style={{
            position: 'fixed',
            bottom: 32,
            right: 32,
            zIndex: 1001,
            maxWidth: 400,
            width: '90vw',
            border: '1px solid #e5e7eb',
            borderRadius: 12,
            background: '#fff',
            boxShadow: '0 2px 16px rgba(0,0,0,0.18)',
            padding: 0,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #e5e7eb', background: '#2563eb', borderRadius: '12px 12px 0 0' }}>
            <span style={{ color: '#fff', fontWeight: 600, fontSize: 18 }}>Chatbot</span>
            <button
              onClick={() => setOpen(false)}
              style={{ background: 'none', border: 'none', color: '#fff', fontSize: 22, cursor: 'pointer' }}
              aria-label="Close chatbot"
            >
              ×
            </button>
          </div>
          <div style={{ padding: 16, minHeight: 320, maxHeight: 420, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 12 }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  background: msg.sender === 'user' ? '#2563eb' : '#f1f5f9',
                  color: msg.sender === 'user' ? '#fff' : '#222',
                  borderRadius: msg.sender === 'user' ? '16px 16px 0 16px' : '16px 16px 16px 0',
                  padding: '12px 16px',
                  maxWidth: '80%',
                  fontSize: '1.05rem',
                  marginBottom: 2
                }}
              >
                {msg.text}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
          <form onSubmit={handleSend} style={{ display: 'flex', gap: 8, padding: 12, borderTop: '1px solid #e5e7eb', background: '#f8fafc' }}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type your message..."
              style={{ flex: 1, padding: 10, borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '1rem', outline: 'none' }}
              disabled={loading}
            />
            <button
              type="submit"
              style={{ background: '#2563eb', color: '#fff', border: 'none', borderRadius: 8, padding: '0 18px', fontSize: '1.1rem', cursor: 'pointer', height: 40 }}
              disabled={loading}
            >
              {loading ? '...' : 'Send'}
            </button>
          </form>
        </div>
      )}
    </>
  );
}

export default Chatbot;
