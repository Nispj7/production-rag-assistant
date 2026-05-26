import React from 'react';

const Header = () => {
  return (
    <header className="glass-panel" style={{ padding: '20px 30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
        <div style={{
          width: '40px', height: '40px', borderRadius: '10px',
          background: 'linear-gradient(135deg, var(--primary-accent), var(--secondary-accent))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 'bold', fontSize: '20px', color: 'white',
          boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)'
        }}>
          AI
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 600 }}>Knowledge Assistant</h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>RAG System Engine</p>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div className="animate-pulse" style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success-color)' }}></div>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Backend Connected</span>
      </div>
    </header>
  );
};

export default Header;
