import React, { useState } from 'react';
import './CitationDetail.css';

function CitationDetail({ citation, onClose }) {
  if (!citation) {
    return null;
  }

  const { citation_id, type, row_index, row_data, citation_number } = citation;

  return (
    <div className="citation-detail-overlay" onClick={onClose}>
      <div className="citation-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="citation-header">
          <h2>Citation Details [#{citation_number}]</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="citation-body">
          <div className="citation-meta">
            <div className="meta-item">
              <span className="meta-label">Citation ID:</span>
              <span className="meta-value">{citation_id}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Source Type:</span>
              <span className="meta-value">
                {type === 'sql' ? '📊 Database Query' : '🌲 Semantic Search'}
              </span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Row Index:</span>
              <span className="meta-value">#{row_index}</span>
            </div>
          </div>

          <div className="citation-data">
            <h3>Full Record Data:</h3>
            <div className="data-table">
              {row_data && Object.entries(row_data).map(([key, value]) => (
                <div key={key} className="data-row">
                  <div className="data-key">{key}</div>
                  <div className="data-value">
                    {value && typeof value === 'object' 
                      ? JSON.stringify(value) 
                      : String(value)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="citation-note">
            <p>
              This data point is sourced from the{' '}
              <strong>
                {type === 'sql' 
                  ? 'California Safe Cosmetics Database' 
                  : 'Semantic Vector Search'}
              </strong>
              . Row #{row_index} from the query results.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CitationDetail;
