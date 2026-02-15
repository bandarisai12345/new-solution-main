import React, { useState } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSendMessage = async (userMessage) => {
    // Add user message to chat
    const newMessages = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);
    setError('');
    setLoading(true);

    try {
      // Call FastAPI backend with streaming enabled
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userMessage,
          stream: true,  // Enable streaming
          limit_results: 6,  // Limit to 6 SQL results
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      const data = await response.json();

      // Debug: Log the response to see what we're getting
      console.log('API Response:', data);
      console.log('SQL Results:', data.sql_results);
      console.log('Semantic Results:', data.semantic_results);

      // Add assistant response with all data
      newMessages.push({
        role: 'assistant',
        content: data.answer,
        citations: data.citations,  // Include citations for reference
        sqlResults: data.sql_results,  // SQL table results
        semanticResults: data.semantic_results,  // Semantic search table results
        sqlQuery: data.sql_query_used,  // SQL query used
        explanation: data.explanation,
        intent: data.intent
      });

      setMessages(newMessages);
    } catch (err) {
      setError(`Error: ${err.message}`);
      newMessages.push({
        role: 'assistant',
        content: `Sorry, I encountered an error: ${err.message}`,
      });
      setMessages(newMessages);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="header-content">
          <h1>
            <span className="logo-icon">🧪</span>
            Cosmetics  Assistant
          </h1>
          <p className="subtitle">AI-powered search for California cosmetics & ingredients</p>
        </div>
      </header>

      <main className="main-container">
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          loading={loading}
          error={error}
        />
      </main>
    </div>
  );
}

export default App;
