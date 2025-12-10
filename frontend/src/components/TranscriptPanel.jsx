import React, { useRef, useEffect } from 'react';
import './TranscriptPanel.css';

const TranscriptPanel = ({ messages }) => {
    const endRef = useRef(null);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="card transcript-panel">
            <h3>Transcript</h3>
            <div className="messages-list">
                {messages.length === 0 && <p className="text-muted">No conversation yet.</p>}
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role.toLowerCase()}`}>
                        <strong>{msg.role}:</strong> {msg.text}
                    </div>
                ))}
                <div ref={endRef} />
            </div>
        </div>
    );
};

export default TranscriptPanel;
