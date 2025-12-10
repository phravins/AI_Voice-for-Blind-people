import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, ChevronLeft, ChevronRight, Home as HomeIcon } from 'lucide-react';
import VoiceBar from '../components/VoiceBar';
import ContextCard from '../components/ContextCard';
import TranscriptPanel from '../components/TranscriptPanel';
import ActionToast from '../components/ActionToast';
import { getPageContent, sendAction, getAudioUrl } from '../utils/api';
import { VoiceManager, playAudioCallback, playChime as playChimeLocal } from '../utils/voice';
import './Tutor.css';

const voiceManager = new VoiceManager();

const Tutor = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { docId, filename, page_count, message, audio_url } = location.state || {};

    const [page, setPage] = useState(0);
    const [pageText, setPageText] = useState(null);
    const [messages, setMessages] = useState([]);
    const [voiceState, setVoiceState] = useState('IDLE');
    const [toast, setToast] = useState(null);
    const [currentAudio, setCurrentAudio] = useState(null);

    // Track confirmation if we are in a continuous conversation loop
    const [isContinuousMode, setIsContinuousMode] = useState(false);
    // Use Ref to access latest state in closures (like audio.onended)
    const isContinuousModeRef = React.useRef(isContinuousMode);
    useEffect(() => { isContinuousModeRef.current = isContinuousMode; }, [isContinuousMode]);

    const [showTranslate, setShowTranslate] = useState(false);

    // Initial Load
    useEffect(() => {
        if (!docId) {
            navigate('/');
            return;
        }
        loadPage(0);

        // Auto-start Wake Mode if requested
        const { autoStart } = location.state || {};
        if (autoStart) {
            setTimeout(() => {
                if (voiceState === 'IDLE') {
                    setIsContinuousMode(true);
                    startWakeListening();
                    setToast({ message: "Hands-Free Voice Control Active", type: "success" });
                }
            }, 500);
        }

        if (message) {
            addMessage('System', message);
            if (audio_url) {
                playResponse(audio_url);
            } else {
                playChimeLocal('start');
            }
        }
    }, [docId]);

    const loadPage = async (pageNum) => {
        setPageText(null);
        try {
            const data = await getPageContent(docId, pageNum);
            setPageText(data.text || "");
            setPage(data.page);
        } catch (e) {
            setToast({ message: "Failed to load page", type: "error" });
            setPageText("");
        }
    };

    const addMessage = (role, text) => {
        setMessages(prev => [...prev, { role, text }]);
    };

    const handleMicClick = (mode = 'normal') => {
        if (mode === 'wake') {
            setIsContinuousMode(true);
            startWakeListening();
            return;
        }
        if (mode === 'stop_wake') {
            setIsContinuousMode(false);
            stopListening(); // Resets to IDLE
            return;
        }

        if (voiceState === 'IDLE' || voiceState === 'SPEAKING' || voiceState === 'WAKE_STANDBY') {
            if (currentAudio) {
                currentAudio.pause();
                setCurrentAudio(null);
            }
            startListening();
        } else if (voiceState === 'LISTENING') {
            stopListening();
        }
    };

    const startWakeListening = () => {
        setVoiceState('WAKE_STANDBY');
        voiceManager.start(
            (text, isFinal) => {
                if (text === 'WAKE_DETECTED') {
                    setToast({ message: "Wake Detected!", type: "success" });
                    handleVoiceCommand("Wake");
                } else if (isFinal && text.toLowerCase().includes('stop')) {
                    // Handle STOP command - just pause audio, stay in wake mode
                    if (currentAudio) {
                        currentAudio.pause();
                        setCurrentAudio(null);
                        setToast({ message: "Stopped. Say 'Start' to continue.", type: "info" });
                    }
                    // Don't change state - stay in WAKE_STANDBY automatically
                }
            },
            (error) => {
                console.log("Wake standby error:", error);
                if (error === 'not-allowed' || error === 'service-not-allowed') {
                    setToast({ message: "Microphone blocked. Please check browser settings.", type: "error" });
                    setVoiceState('IDLE');
                }
            },
            () => { },
            true,
            'wake'
        );
    };

    const startListening = () => {
        // VoiceManager.start now handles race conditions internally, 
        // but we add a small UI delay to ensure the user is ready.
        setTimeout(() => {
            setVoiceState('LISTENING');
            playChimeLocal('start');

            voiceManager.start(
                (text, isFinal) => {
                    // Interim Feedback
                    if (!isFinal) {
                        setToast({ message: `I hear: "${text}..."`, type: "info" });
                        return;
                    }

                    // Final Command Processing
                    // Logic to handle command
                    if (text.toLowerCase().includes("stop") || text.toLowerCase().includes("exit")) {
                        stopListening();
                        setIsContinuousMode(false);
                        return;
                    }

                    // Only stop now that we have the full sentence
                    stopListening(false);
                    handleVoiceCommand(text);
                },
                (error) => {
                    console.warn("Listening error:", error);
                    setVoiceState('IDLE');
                    // Only error chime if it's a real error, not no-speech
                    if (error !== 'no-speech') playChimeLocal('error');

                    // Critical: If in continuous mode, we MUST restart even after error
                    if (isContinuousMode) {
                        setTimeout(() => startWakeListening(), 500);
                    }
                },
                () => {
                    // On End
                    if (voiceState === 'LISTENING') setVoiceState('IDLE');
                },
                false, // Continuous? No, valid commands are single short phrases usually.
                null   // No wake word, active listening
            );
        }, 200);
    };

    const stopListening = (resetToIdle = true) => {
        voiceManager.stop();
        if (resetToIdle) setVoiceState('IDLE');
        else setVoiceState('PROCESSING');
    };

    const handleVoiceCommand = async (text) => {
        addMessage('User', text);
        setVoiceState('PROCESSING');

        // Specific feedback for potential long-running tasks
        if (text.toLowerCase().includes("pdf") || text.toLowerCase().includes("document")) {
            setToast({ message: "Reading document... this may take a moment.", type: "info" });
        }

        try {
            const res = await sendAction(docId, page, null, text);
            processResponse(res);
        } catch (e) {
            setToast({ message: "Action failed", type: "error" });
            setVoiceState('IDLE');
            playChimeLocal('error');
            if (isContinuousMode) startWakeListening();
        }
    };

    const handleQuickAction = async (intent, entities = {}) => {
        if (intent === 'TRANSLATE' && !entities.target_language) {
            setShowTranslate(true);
            return;
        }

        if (currentAudio) {
            currentAudio.pause();
            setCurrentAudio(null);
        }
        setVoiceState('PROCESSING');
        try {
            const res = await sendAction(docId, page, intent, null, entities);
            processResponse(res);
        } catch (e) {
            setToast({ message: "Action failed", type: "error" });
            setVoiceState('IDLE');
        }
    };

    const processResponse = (res) => {
        if (!res) {
            setVoiceState('IDLE');
            setToast({ message: "Empty response from server", type: "error" });
            if (isContinuousMode) startWakeListening();
            return;
        }

        if (res.new_page !== undefined && res.new_page !== page) {
            loadPage(res.new_page);
        }
        if (res.text_response) {
            addMessage('Assistant', res.text_response);

            // If it's a translation, ALSO update the main reader box
            if (res.type === 'translation') {
                setPageText(res.text_response);
            }
        }

        if (res.type === 'open_document' && res.payload?.doc_id) {
            // Switch document!
            // We need to navigate to current route but with new state.
            // We don't have full metadata (page count) here easily unless we fetch it, 
            // but Tutor.jsx re-fetches content on loadPage(0).
            // Let's navigate to home then back? No, just navigate to self.
            // Best way: Update docId state?
            // Tutor depends on location.state. We should navigate() to /tutor with new state.
            // We need to fetch basic metadata (page count) first? 
            // Or we can just let Tutor component handle it if we trust getPageContent to error if needed.
            // Let's assume we navigate to /tutor with just docId and filename (derived).
            const newId = res.payload.doc_id;
            navigate('/tutor', {
                state: {
                    docId: newId,
                    filename: newId + ".pdf", // Approximate
                    autoStart: true // Keep listening!
                }
            });
            window.location.reload(); // Force reload to ensure clean state? Or React router handles it?
            // React router won't trigger full remount if path same. 
            // Using replace: true or just updating state might be better.
            return;
        }

        if (res.audio_url) {
            playResponse(res.audio_url);
        } else {
            if (isContinuousMode) setTimeout(() => startListening(), 500);
            else startWakeListening(); // Go back to waiting for "Start"
        }
    };

    const playResponse = (url) => {
        setVoiceState('SPEAKING');

        // Stop any existing listening to prevent interference during playback setup
        voiceManager.stop();

        try {
            const fullUrl = getAudioUrl(url);
            const audio = new Audio(fullUrl);
            setCurrentAudio(audio);

            // Barge-in Listener: Listens JUST for "Stop" or "Wait"
            // We do NOT want it to pick up random noise as commands here.
            voiceManager.start(
                (text) => {
                    // Barge-in detected
                    console.log("Barge-in text:", text);
                    if (text.toLowerCase().includes("stop") ||
                        text.toLowerCase().includes("quiet") ||
                        text.toLowerCase().includes("wait")) {

                        audio.pause();
                        audio.currentTime = 0;
                        setCurrentAudio(null);
                        voiceManager.stop();

                        setIsContinuousMode(false); // Assume user wants us to stop everything
                        setVoiceState('IDLE');
                        addMessage('User', "Stop (Barge-in)");
                    }
                    // Note: We ignore other text during playback to avoid "talking to yourself" loops
                },
                (err) => { }, // Ignore errors during speech playback
                () => { },    // Ignore end events
                true          // Continuous
            );

            audio.onended = () => {
                setCurrentAudio(null);
                voiceManager.stop();

                // CRITICAL: Transition back to listening if in continuous mode
                // Use Ref ensure we have the LATEST value, not the one from closure creation
                if (isContinuousModeRef.current) {
                    console.log("Audio ended, restarting loop...");
                    // Small delay to ensure mic is ready
                    setTimeout(() => startListening(), 300);
                } else {
                    setVoiceState('IDLE');
                }
            };

            audio.onerror = (e) => {
                console.error("Audio playback error", e);
                setVoiceState('IDLE');
                setCurrentAudio(null);
                voiceManager.stop();
                if (isContinuousMode) startWakeListening();
            };

            const playPromise = audio.play();
            if (playPromise !== undefined) {
                playPromise.catch(e => {
                    console.error("Audio play failed:", e);
                    setVoiceState('IDLE');
                    voiceManager.stop();
                    // Recover
                    if (isContinuousMode) startWakeListening();
                });
            }
        } catch (e) {
            console.error("Audio Setup Error", e);
            setVoiceState('IDLE');
        }
    };

    const LANGUAGES = ["Tamil", "Hindi", "Spanish", "French", "German", "Chinese", "Japanese"];

    return (
        <div className="tutor-layout">
            {showTranslate && (
                <div className="modal-overlay" onClick={() => setShowTranslate(false)}>
                    <div className="modal-content glass-panel" onClick={e => e.stopPropagation()}>
                        <h3>Select Language</h3>
                        <div className="lang-grid">
                            {LANGUAGES.map(lang => (
                                <button key={lang} className="btn btn-outline"
                                    onClick={() => {
                                        setShowTranslate(false);
                                        handleQuickAction('TRANSLATE', { target_language: lang });
                                    }}>
                                    {lang}
                                </button>
                            ))}
                        </div>
                        <button className="btn btn-ghost mt-4" onClick={() => setShowTranslate(false)}>Cancel</button>
                    </div>
                </div>
            )}
            <header className="glass-panel nav-header">
                <div className="header-left">
                    <button className="btn btn-ghost" onClick={() => navigate('/')}>
                        <ArrowLeft size={20} /> Back
                    </button>
                    <h2 className="doc-title">{filename}</h2>
                </div>
                <div className="header-right">
                    <button className="btn btn-outline btn-sm" onClick={() => setShowTranslate(true)} title="Translate this page">
                        Translate
                    </button>
                    <span className="page-indicator badge">Page {page + 1} / {page_count || '?'}</span>
                </div>
            </header>

            <div className="tutor-content">
                {/* Left Column: Reader */}
                <section className="reader-section glass-panel">
                    <div className="page-content">
                        {pageText === null ? (
                            <div className="loading-placeholder">Loading page...</div>
                        ) : pageText.length === 0 ? (
                            <div className="empty-state-placeholder">
                                <p>No text found on this page.</p>
                                <small>This might be an image-only PDF. Please try a text-based PDF.</small>
                            </div>
                        ) : (
                            <div className="text-content">{pageText}</div>
                        )}
                    </div>
                    <div className="page-controls-footer">
                        <button className="btn btn-secondary" disabled={page === 0} onClick={() => handleQuickAction('NAVIGATE_PREV')}>
                            <ChevronLeft /> Previous Page
                        </button>
                        <button className="btn btn-secondary" onClick={() => handleQuickAction('NAVIGATE_NEXT')}>
                            Next Page <ChevronRight />
                        </button>
                    </div>
                </section>

                {/* Right Column: Context & Transcript */}
                <aside className="context-section">
                    <div className="glass-panel context-container">
                        <ContextCard
                            title={`Page ${page + 1} Insights`}
                            onAction={(intent) => handleQuickAction(intent)}
                        />
                    </div>
                    <div className="glass-panel transcript-container">
                        <TranscriptPanel messages={messages} />
                    </div>
                </aside>
            </div>

            <VoiceBar state={voiceState} onMicClick={handleMicClick} />
            {toast && <ActionToast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        </div>
    );
};

export default Tutor;
