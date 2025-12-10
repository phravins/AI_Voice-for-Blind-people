export class VoiceManager {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.silenceTimer = null; // Timer for auto-submit

        if ('webkitSpeechRecognition' in window) {
            this.recognition = new window.webkitSpeechRecognition();
            this.recognition.continuous = false; // We manage restart manually for better control
            this.recognition.interimResults = true; // ALWAYS True for responsiveness
            this.recognition.lang = 'en-US';
        }
    }

    async start(onResult, onError, onEnd, continuous = false, wakeWord = null) {
        if (!this.recognition) {
            if (onError) onError("Speech recognition not supported");
            return;
        }

        // Prevent race condition: if already listening, force close and WAIT
        if (this.isListening) {
            console.log("VoiceManager: Already active, resetting...");
            this.stop();
            // Wait for state to clear
            await new Promise(r => setTimeout(r, 100));
        }

        try {
            this.recognition.abort();
        } catch (e) { }

        this.isListening = true;
        this.recognition.continuous = continuous;
        this.recognition.interimResults = true; // Forced True

        // Important: Language handling
        this.recognition.lang = 'en-US';

        this.recognition.onresult = (event) => {
            // Clear silence timer on every new speech packet
            if (this.silenceTimer) clearTimeout(this.silenceTimer);

            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            const combined = finalTranscript || interimTranscript;
            // "Final" implies the engine is sure, but we also enforce our own silence timeout
            const isEngineFinal = !!finalTranscript;

            if (wakeWord) {
                // Wake detection is aggressive, check partials
                const lower = combined.toLowerCase();
                if (lower.includes(wakeWord.toLowerCase()) ||
                    lower.includes("wake up") ||
                    lower.includes("hey") ||
                    lower.includes("start")) {
                    console.log("Wake word detected:", combined);
                    if (onResult) onResult("WAKE_DETECTED", true);
                    return;
                }
            } else {
                // Normal Command Mode
                // 1. Send feedback
                if (onResult) onResult(combined.trim(), isEngineFinal);

                // 2. Silence Detection Logic
                // If we have text but it's not "final" yet, wait 1.5s then FORCE it.
                if (combined.trim().length > 0 && !isEngineFinal) {
                    this.silenceTimer = setTimeout(() => {
                        console.log("Silence detected (1s), forcing submission:", combined);
                        if (onResult) onResult(combined.trim(), true); // Force Final = True
                    }, 1000); // 1 second for fast response
                }
            }
        };

        this.recognition.onerror = (event) => {
            // Clear timer on error
            if (this.silenceTimer) clearTimeout(this.silenceTimer);

            if (event.error === 'no-speech') return; // Ignore standard no-speech
            if (event.error === 'aborted') return;   // Ignore manual stops

            console.warn("Speech error:", event.error);
            if (onError) onError(event.error);
        };

        this.recognition.onend = () => {
            // Clear timer on end
            if (this.silenceTimer) clearTimeout(this.silenceTimer);

            // Only auto-restart if we are STILL supposed to be listening (flag is true)
            // and we are in continuous mode.
            if (this.isListening && continuous) {
                console.log("Auto-restarting speech recognition (Continuous Mode)...");
                setTimeout(() => {
                    try {
                        this.recognition.start();
                    } catch (e) {
                        // Ignore "already started" errors during restart phase
                    }
                }, 200);
            } else {
                this.isListening = false;
                if (onEnd) onEnd();
            }
        };

        try {
            this.recognition.start();
        } catch (e) {
            console.warn("Speech start warning:", e.message);
            this.isListening = true;
        }
    }

    stop() {
        this.isListening = false; // Flag to stop auto-restart
        if (this.silenceTimer) clearTimeout(this.silenceTimer);

        if (this.recognition) {
            try {
                this.recognition.stop();
            } catch (e) {
                console.error("Stop error", e);
            }
        }
    }
}

export const playAudioCallback = (url, onEnded) => {
    const audio = new Audio(url);
    audio.onended = onEnded;
    audio.play().catch(e => console.error("Audio play error", e));
    return audio; // Return to allow pause/stop
};

export const playChime = (type) => {
    // Standard beep logic
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    const now = audioContext.currentTime;

    if (type === 'start') {
        oscillator.frequency.setValueAtTime(440, now);
        oscillator.frequency.exponentialRampToValueAtTime(880, now + 0.1);
        gainNode.gain.setValueAtTime(0.1, now);
        gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
        oscillator.start(now);
        oscillator.stop(now + 0.1);
    } else if (type === 'success') {
        oscillator.frequency.setValueAtTime(880, now);
        gainNode.gain.setValueAtTime(0.1, now);
        gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
        oscillator.start(now);
        oscillator.stop(now + 0.2);
    } else if (type === 'error') {
        oscillator.type = 'sawtooth';
        oscillator.frequency.setValueAtTime(150, now);
        gainNode.gain.setValueAtTime(0.2, now);
        gainNode.gain.linearRampToValueAtTime(0.01, now + 0.3);
        oscillator.start(now);
        oscillator.stop(now + 0.3);
    }
};
