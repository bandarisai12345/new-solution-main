import React from 'react';
import './CitationPanel.css';

function CitationPanel({ sources }) {
  const formatSource = (source) => {
    if (source.type === 'sql') {
      return {
        title: '📊 SQL Database',
        description: source.source || 'California Safe Cosmetics Database',
        details: 'Structured data query'
      };
    } else if (source.type === 'semantic' || source.type === 'semantic_filtered') {
      return {
        title: '🌲 Semantic Search',
        description: source.product || 'Pinecone Vector Database',
        details: [
          source.company && `Company: ${source.company}`,
          source.chemical && `Chemical: ${source.chemical}`
        ].filter(Boolean).join(' • ')
      };
    }
    return null;
  };

  const uniqueSources = [];
  const seen = new Set();

  sources.forEach(source => {
    const key = JSON.stringify(source);
    if (!seen.has(key)) {
      seen.add(key);
      uniqueSources.push(source);
    }
  });

  return (
    <div className="citation-panel">
      <div className="panel-header">
        <h2>📚 Sources & Citations</h2>
        <p className="panel-subtitle">Data sources used in this response</p>
      </div>

      <div className="sources-list">
        {uniqueSources.length === 0 ? (
          <div className="no-sources">
            <p>🔍 Sources will appear here</p>
            <p className="hint">Ask a question to see where the data comes from</p>
          </div>
        ) : (
          <>
            {uniqueSources.map((source, idx) => {
              const formatted = formatSource(source);
              if (!formatted) return null;

              return (
                <div key={idx} className="source-card">
                  <div className="source-header">
                    <h3>{formatted.title}</h3>
                  </div>
                  <div className="source-body">
                    <p className="source-description">{formatted.description}</p>
                    {formatted.details && (
                      <p className="source-details">{formatted.details}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </>
        )}
      </div>

      <div className="sources-info">
        <div className="info-item">
          <span className="info-icon">📊</span>
          <span>SQL Database</span>
        </div>
        <div className="info-item">
          <span className="info-icon">🌲</span>
          <span>Semantic Search</span>
        </div>
        <div className="info-item">
          <span className="info-icon">🧠</span>
          <span>AI-Powered Analysis</span>
        </div>
      </div>
    </div>
  );
}

export default CitationPanel;
