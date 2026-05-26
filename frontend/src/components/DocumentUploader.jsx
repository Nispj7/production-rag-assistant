import React, { useState, useRef } from 'react';

const DocumentUploader = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // { type: 'success' | 'error', message: string }
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileUpload = async (file) => {
    setIsUploading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/v1/document/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setUploadStatus({ type: 'success', message: `Successfully indexed ${data.chunk_count} chunks from ${file.name}.` });
        if (onUploadSuccess) onUploadSuccess();
      } else {
        setUploadStatus({ type: 'error', message: data.detail || 'Upload failed.' });
      }
    } catch (error) {
      setUploadStatus({ type: 'error', message: 'Failed to connect to the server.' });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '30px', marginBottom: '30px', textAlign: 'center' }}>
      <h2 style={{ marginBottom: '15px', fontSize: '1.2rem' }}>Index New Document</h2>
      
      <div 
        onClick={() => fileInputRef.current?.click()}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${isDragging ? 'var(--primary-accent)' : 'var(--border-color)'}`,
          borderRadius: '12px',
          padding: '40px 20px',
          cursor: 'pointer',
          background: isDragging ? 'rgba(99, 102, 241, 0.05)' : 'transparent',
          transition: 'all 0.3s ease'
        }}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          accept=".txt,.pdf,.docx" 
          onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
        />
        
        {isUploading ? (
          <div className="animate-pulse" style={{ color: 'var(--primary-accent)' }}>
            Processing document vectors...
          </div>
        ) : (
          <div>
            <div style={{ fontSize: '2rem', marginBottom: '10px' }}>📄</div>
            <p style={{ color: 'var(--text-muted)' }}>Drag and drop a PDF, TXT, or DOCX file here, or click to browse</p>
          </div>
        )}
      </div>

      {uploadStatus && (
        <div 
          className="animate-fade-in" 
          style={{ 
            marginTop: '15px', 
            padding: '10px', 
            borderRadius: '8px',
            fontSize: '0.9rem',
            background: uploadStatus.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            color: uploadStatus.type === 'success' ? 'var(--success-color)' : 'var(--error-color)',
            border: `1px solid ${uploadStatus.type === 'success' ? 'var(--success-color)' : 'var(--error-color)'}`
          }}
        >
          {uploadStatus.message}
        </div>
      )}
    </div>
  );
};

export default DocumentUploader;
