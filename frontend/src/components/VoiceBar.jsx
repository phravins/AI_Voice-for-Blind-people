import React from 'react';
import { Mic, MicOff, Loader2, Volume2 } from 'lucide-react';
import './VoiceBar.css';

const VoiceBar = ({ state, onMicClick, text }) => {
    // state: 'IDLE' | 'LISTENING' | 'PROCESSING' | 'SPEAKING'

    return (
        <div className="voice-bar-container">
            {state === 'LISTENING' && (
                <div className="visual-waveform">
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                </div>
            )}

            <div className="voice-status-label">
                {state === 'LISTENING' && 'Listening...'}
                {state === 'WAKE_STANDBY' && 'Standby: Say "Wake"'}
                {state === 'PROCESSING' && 'Thinking...'}
                {state === 'SPEAKING' && 'Speaking...'}
                {state === 'IDLE' && (text || 'Press Mic to Start')}
            </div>

            <button
                className={`mic-button ${state === 'LISTENING' ? 'active' : ''} ${state === 'PROCESSING' ? 'processing' : ''} ${state === 'WAKE_STANDBY' ? 'standby' : ''}`}
                onClick={() => {
                    // If in Standby, stop it. If Idle, start Wake Standby.
                    if (state === 'WAKE_STANDBY') onMicClick('stop_wake');
                    else if (state === 'IDLE') onMicClick('wake');
                    else onMicClick(); // For other states, handle normally (likely stop)
                }}
                aria-label="Toggle Voice Control"
                disabled={state === 'PROCESSING'}
            >
                {state === 'PROCESSING' ? (
                    <Loader2 className="spin" size={32} />
                ) : state === 'SPEAKING' ? (
                    <Volume2 size={32} />
                ) : state === 'WAKE_STANDBY' ? (
                    <Mic size={32} className="pulse-slow" color="#2563eb" />
                ) : (
                    <MicOff size={32} style={{ opacity: 0.4 }} />
                )}
            </button>
            <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#666' }}>
                {state === 'IDLE' ? 'Click to Enable Hands-Free' : state === 'WAKE_STANDBY' ? 'Hands-Free Active' : ''}
            </div>
        </div>
    );
};

export default VoiceBar;
