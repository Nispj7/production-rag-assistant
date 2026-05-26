import React from 'react';
import Header from './components/Header';
import DocumentUploader from './components/DocumentUploader';
import ChatInterface from './components/ChatInterface';

function App() {
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '40px 20px', width: '100%' }}>
      <Header />
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'minmax(300px, 1fr) minmax(400px, 2fr)', 
        gap: '30px',
        alignItems: 'start'
      }}>
        {/* Left Column: Tools & Uploader */}
        <div>
          <DocumentUploader />
          
          <div className="glass-panel" style={{ padding: '20px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            <h3 style={{ color: 'var(--text-main)', marginBottom: '10px' }}>System Architecture</h3>
            <ul style={{ listStylePosition: 'inside', lineHeight: '1.8' }}>
              <li><strong>Frontend:</strong> React + Vite</li>
              <li><strong>Styling:</strong> Vanilla CSS Glassmorphism</li>
              <li><strong>Backend:</strong> FastAPI</li>
              <li><strong>Vector Store:</strong> FAISS (Offline)</li>
              <li><strong>Model:</strong> Local Extractive QA</li>
            </ul>
          </div>
        </div>

        {/* Right Column: Chat Interface */}
        <div>
          <ChatInterface />
        </div>
      </div>
    </div>
  );
}

export default App;
