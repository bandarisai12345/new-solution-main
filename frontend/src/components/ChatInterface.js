import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';
import CitationDetail from './CitationDetail';

// Utility function to format text like Gemini UI
const formatResponseText = (text) => {
  if (!text) return '';

  let formatted = text;

  // Bold
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Italic
  formatted = formatted.replace(/_(.+?)_/g, '<em>$1</em>');

  // Inline code
  formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Headers
  formatted = formatted.replace(/### (.*?)(\n|$)/g, '<h3><strong>$1</strong></h3>');
  formatted = formatted.replace(/## (.*?)(\n|$)/g, '<h2><strong>$1</strong></h2>');
  formatted = formatted.replace(/# (.*?)(\n|$)/g, '<h1><strong>$1</strong></h1>');

  // Bullet & numbered lists
  const lines = formatted.split('\n');
  let inList = false;
  let inNumberedList = false;
  const processedLines = [];

  lines.forEach((line) => {
    const bulletMatch = line.match(/^[-•*]\s+(.*)$/);
    const numberedMatch = line.match(/^\d+\.\s+(.*)$/);

    if (bulletMatch) {
      if (!inList) {
        processedLines.push('<ul>');
        inList = true;
      }
      processedLines.push(`<li>${bulletMatch[1]}</li>`);
    } else if (numberedMatch) {
      if (!inNumberedList) {
        processedLines.push('<ol>');
        inNumberedList = true;
      }
      processedLines.push(`<li>${numberedMatch[1]}</li>`);
    } else {
      if (inList) {
        processedLines.push('</ul>');
        inList = false;
      }
      if (inNumberedList) {
        processedLines.push('</ol>');
        inNumberedList = false;
      }
      processedLines.push(line);
    }
  });

  if (inList) processedLines.push('</ul>');
  if (inNumberedList) processedLines.push('</ol>');

  formatted = processedLines.join('\n');

  // Line breaks
  formatted = formatted.replace(/\n/g, '<br/>');

  return formatted;
};

function ChatInterface({ messages, onSendMessage, loading, error }) {
  const [input, setInput] = useState('');
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [citationMap, setCitationMap] = useState({});
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Update citation map
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === 'assistant' && lastMessage.citations) {
        const cMap = {};
        lastMessage.citations.forEach((citation) => {
          cMap[citation.citation_number] = citation;
        });
        setCitationMap(cMap);
      }
    }
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Inline citation rendering
  const renderMessageWithCitations = (content) => {
    if (!content) return content;

    const parts = [];
    const regex = /\[(\d+)\]/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          text: content.substring(lastIndex, match.index),
        });
      }

      const citationNum = parseInt(match[1], 10);
      const citation = citationMap[citationNum];

      parts.push({
        type: 'citation',
        citationNum,
        citation,
      });

      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < content.length) {
      parts.push({
        type: 'text',
        text: content.substring(lastIndex),
      });
    }

    return parts.map((part, idx) => {
      if (part.type === 'text') {
        return (
          <React.Fragment key={idx}>
            {part.text.split('\n').map((line, lineIdx) => (
              <React.Fragment key={lineIdx}>
                {line}
                {lineIdx < part.text.split('\n').length - 1 && <br />}
              </React.Fragment>
            ))}
          </React.Fragment>
        );
      } else {
        return (
          <span
            key={idx}
            className="citation-link"
            onClick={() => part.citation && setSelectedCitation(part.citation)}
            title={part.citation ? 'View citation details' : 'Citation unavailable'}
          >
            [{part.citationNum}]
          </span>
        );
      }
    });
  };

  const formatMessage = (content) => {
    if (!content) return '';
    const formatted = formatResponseText(content);
    return (
      <div
        className="formatted-response"
        dangerouslySetInnerHTML={{ __html: formatted }}
      />
    );
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <div className="ai-ball-wrapper">
              <div className="ai-ball"></div>
            </div>
            <h2>Cosmetics Assistant</h2>
            <p>Your intelligent product & ingredient search companion.</p>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {msg.role === 'assistant' && msg.citations
                      ? renderMessageWithCitations(msg.content)
                      : formatMessage(msg.content)}
                  </div>

                  {msg.sqlResults && msg.sqlResults.length > 0 && (
                    <div className="results-section">
                      <h4>📊 Database Results ({msg.sqlResults.length} rows)</h4>
                      <div className="results-table">
                        <table>
                          <thead>
                            <tr>
                              {Object.keys(msg.sqlResults[0]).map((key) => (
                                <th key={key}>{key}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {msg.sqlResults.map((row, rowIdx) => (
                              <tr key={rowIdx}>
                                {Object.values(row).map((val, valIdx) => (
                                  <td key={valIdx}>{String(val)}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {msg.semanticResults && msg.semanticResults.length > 0 && (
                    <div className="results-section">
                      <h4>🌲 Semantic Results ({msg.semanticResults.length})</h4>
                      <div className="results-table">
                        <table>
                          <thead>
                            <tr>
                              {Object.keys(msg.semanticResults[0]).map((key) => (
                                <th key={key}>{key}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {msg.semanticResults.map((row, rowIdx) => (
                              <tr key={rowIdx}>
                                {Object.values(row).map((val, valIdx) => (
                                  <td key={valIdx}>{String(val)}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="message assistant loading">
                <div className="message-avatar">🤖</div>
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {error && <div className="error-message">⚠️ {error}</div>}

      <form className="chat-input-area" onSubmit={handleSubmit}>
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about cosmetics, ingredients, companies, brands..."
          disabled={loading}
          rows="3"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="send-button"
        >
          {loading ? '⏳' : '📤'} Send
        </button>
      </form>

      {selectedCitation && (
        <CitationDetail
          citation={selectedCitation}
          onClose={() => setSelectedCitation(null)}
        />
      )}
    </div>
  );
}

export default ChatInterface;
