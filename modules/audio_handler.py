import pygame
import logging
import os
from config import TEMP_AUDIO_DIR

logger = logging.getLogger(__name__)

class AudioHandler:
    """
    Handles low-level audio operations like playing audio files.
    Assumes the audio file is already generated (e.g., by gTTS in speech_processor.py).
    """

    def __init__(self):
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        logger.info("AudioHandler initialized with pygame mixer.")

    def play_audio_file(self, filepath):
        """
        Plays an audio file from the specified path.

        Args:
            filepath (str): The path to the audio file to play.
        """
        if not os.path.exists(filepath):
            logger.error(f"Audio file does not exist: {filepath}")
            return

        try:
            logger.debug(f"Loading audio file: {filepath}")
            pygame.mixer.music.load(filepath)
            logger.debug("Playing audio file...")
            pygame.mixer.music.play()

            # Wait until the music finishes playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)  # Check every 100ms

            logger.debug("Finished playing audio file.")
        except Exception as e:
            logger.error(f"Error playing audio file {filepath}: {e}")

    def stop_current_audio(self):
        """Stops the currently playing audio."""
        try:
            pygame.mixer.music.stop()
            logger.debug("Stopped current audio playback.")
        except Exception as e:
            logger.error(f"Error stopping audio: {e}")

    def cleanup(self):
        """Quits the pygame mixer, freeing resources."""
        try:
            pygame.mixer.quit()
            logger.info("AudioHandler mixer quit successfully.")
        except Exception as e:
            logger.error(f"Error during AudioHandler cleanup: {e}")

# --- Optional: Helper function for playing temporary files directly ---
def play_temp_audio_file(filename):
    """
    Convenience function to play an audio file located in the TEMP_AUDIO_DIR.
    """
    full_path = os.path.join(TEMP_AUDIO_DIR, filename)
    handler = AudioHandler()
    handler.play_audio_file(full_path)
    # Note: It's generally better to manage the handler lifecycle at a higher level
    # if you need to play multiple files or perform other operations.
    handler.cleanup()

# Example usage (for testing this module independently):
# if __name__ == "__main__":
#     handler = AudioHandler()
#     handler.play_audio_file("path/to/your/test.mp3") # Replace with an actual file path
#     handler.cleanup()