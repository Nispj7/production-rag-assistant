import React, { useState, useRef, useEffect } from 'react';
import Citation from './Citation';

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your AI Knowledge Assistant. Upload a document above and ask me questions about it.' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Hardcoded session ID for simplicity in this demo.
  // In production, this might be generated uniquely per browser session.
  const sessionId = 'web-session-1';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          query: userMessage,
          k: 3
        })
      });

      const data = await response.json();

      if (response.ok) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: data.answer,
          citations: data.citations
        }]);
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${data.detail || 'Failed to get response.'}`, isError: true }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Network error. Make sure the backend server is running.', isError: true }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearSession = async () => {
    try {
      await fetch(`http://localhost:8000/api/v1/chat/session/${sessionId}`, { method: 'DELETE' });
      setMessages([{ role: 'assistant', content: 'Conversation history cleared. How else can I help?' }]);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '600px' }}>
      {/* Chat Header */}
      <div style={{ padding: '20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '1.2rem', margin: 0 }}>Conversational RAG</h2>
        <button 
          onClick={handleClearSession}
          style={{ 
            background: 'transparent', 
            border: '1px solid var(--border-color)', 
            color: 'var(--text-muted)',
            padding: '6px 12px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.8rem'
          }}
        >
          Clear Context
        </button>
      </div>

      {/* Messages Area */}
      <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {messages.map((msg, idx) => (
          <div key={idx} className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            
            <div style={{
              maxWidth: '80%',
              padding: '12px 18px',
              borderRadius: '16px',
              borderBottomRightRadius: msg.role === 'user' ? '4px' : '16px',
              borderBottomLeftRadius: msg.role === 'assistant' ? '4px' : '16px',
              background: msg.role === 'user' 
                ? 'linear-gradient(135deg, var(--primary-accent), var(--secondary-accent))' 
                : 'var(--bg-card)',
              border: msg.role === 'assistant' ? '1px solid var(--border-color)' : 'none',
              color: msg.isError ? 'var(--error-color)' : 'white',
              lineHeight: 1.5,
              whiteSpace: 'pre-wrap'
            }}>
              {msg.content}
            </div>

            {/* Citations block for assistant messages */}
            {msg.citations && msg.citations.length > 0 && (
              <div style={{ width: '80%', marginTop: '5px' }}>
                {msg.citations.map((cit, cIdx) => (
                  <Citation key={cIdx} citation={cit} index={cIdx} />
                ))}
              </div>
            )}
            
          </div>
        ))}
        
        {isLoading && (
          <div className="animate-pulse" style={{ alignSelf: 'flex-start', color: 'var(--text-muted)', fontSize: '0.9rem', padding: '10px' }}>
            Synthesizing response...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div style={{ padding: '20px', borderTop: '1px solid var(--border-color)' }}>
        <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: '10px' }}>
          <input 
            type="text" 
            className="input-glass" 
            placeholder="Ask a question about the documents..." 
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" className="btn" disabled={isLoading || !inputValue.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
