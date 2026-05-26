import React, { useState } from 'react';

const Citation = ({ citation, index }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div 
      className="glass-panel" 
      style={{ 
        padding: '10px 15px', 
        marginTop: '10px', 
        fontSize: '0.85rem',
        background: 'rgba(25, 28, 41, 0.4)' // slightly darker for contrast inside chat bubble
      }}
    >
      <div 
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
          <span style={{ 
            background: 'rgba(99, 102, 241, 0.2)', 
            color: 'var(--primary-accent)', 
            padding: '2px 6px', 
            borderRadius: '4px', 
            fontWeight: 600 
          }}>
            [{index + 1}]
          </span>
          <span style={{ fontFamily: 'monospace' }}>{citation.source || 'Unknown Source'}</span>
        </div>
        <div style={{ color: 'var(--primary-accent)', fontSize: '0.75rem', fontWeight: 500 }}>
          {expanded ? 'Hide Content ↑' : 'View Content ↓'}
        </div>
      </div>
      
      {expanded && (
        <div 
          className="animate-fade-in"
          style={{ 
            marginTop: '12px', 
            paddingTop: '12px', 
            borderTop: '1px solid var(--border-color)',
            color: 'var(--text-muted)',
            lineHeight: 1.5,
            whiteSpace: 'pre-wrap'
          }}
        >
          {citation.content_snippet}
        </div>
      )}
    </div>
  );
};

export default Citation;
