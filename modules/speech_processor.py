import speech_recognition as sr
import logging
import os
from gtts import gTTS
# Import the new AudioHandler
from modules.audio_handler import AudioHandler
from config import STT_TIMEOUT, TTS_LANGUAGE, TEMP_AUDIO_DIR

logger = logging.getLogger(__name__)

class SpeechProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        # Optional: Create an AudioHandler instance if needed for more control
        # self.audio_handler = AudioHandler()
        
        # Adjust for ambient noise once at startup
        logger.info("Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
        logger.info("Microphone calibration complete.")

    def listen_for_command(self):
        """Listens for a voice command and returns the recognized text."""
        logger.info("Listening for command...")
        try:
            with self.microphone as source:
                # Play a short beep using pygame or print an indicator
                # For simplicity here, just log.
                logger.info("Beep! (Listening now)")
                audio_data = self.recognizer.listen(source, timeout=STT_TIMEOUT)
            logger.info("Audio captured, attempting recognition...")
            # Using Google Web Speech API
            text = self.recognizer.recognize_google(audio_data)
            logger.info(f"Recognized command: {text}")
            return text
        except sr.WaitTimeoutError:
            logger.warning("Timeout: No speech detected.")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand the audio.")
            return None
        except sr.RequestError as e:
            logger.error(f"Could not request results from speech recognition service; {e}")
            return None

    def speak_text(self, text, lang=TTS_LANGUAGE):
        """Converts text to speech and plays it using AudioHandler."""
        if not text:
            logger.warning("Tried to speak empty text.")
            return

        try:
            logger.debug(f"Generating speech for text: {text[:50]}...") # Log first 50 chars
            tts = gTTS(text=text, lang=lang, slow=False)
            # Generate a unique filename to avoid conflicts if multiple speak calls happen
            import uuid
            unique_filename = f"temp_output_{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(TEMP_AUDIO_DIR, unique_filename)
            tts.save(filepath)

            # Use the AudioHandler to play the file
            audio_handler = AudioHandler() # Create instance for this playback
            audio_handler.play_audio_file(filepath)
            audio_handler.cleanup() # Clean up resources after playback

            # Delete the temporary file after playing
            try:
                os.remove(filepath)
                logger.debug(f"Deleted temporary audio file: {filepath}")
            except OSError as e:
                logger.error(f"Could not delete temporary file {filepath}: {e}")

        except Exception as e:
            logger.error(f"Error during text-to-speech generation or playback: {e}")
            # Ensure cleanup even if an error occurs during TTS generation
            try:
                audio_handler.cleanup()
            except:
                pass # If audio_handler wasn't created, ignore