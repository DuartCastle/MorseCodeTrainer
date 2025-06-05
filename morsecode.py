# Morse Code Trainer - Cross-Platform Version
# Author: Glenn Maclean WA7SPY

# === Import and Check Dependencies ===
try:
    import pygame
except ImportError:
    print("Error: Pygame is not installed. Run: pip install pygame")
    exit(1)

try:
    import numpy as np
except ImportError:
    print("Error: NumPy is not installed. Run: pip install numpy")
    exit(1)

try:
    import pyttsx3
except ImportError:
    print("Error: pyttsx3 is not installed. Run: pip install pyttsx3")
    exit(1)

import random
import signal
import platform
import shutil
import subprocess
import os
import time

# === Initialize Pygame Mixer ===
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
except pygame.error as e:
    print(f"[ERROR] Pygame mixer failed: {e}")
    exit(1)

# === Morse Settings ===
current_frequency = 700
sample_rate = 44100
current_wpm = 10
dot_duration = 60.0 / (current_wpm * 50.0)
show_morse = True
voice_enabled = False

# === Morse Code Dictionary ===
morse_code = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
    'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--',
    '?': '..--..', '/': '-..-.', '-': '-....-', '(': '-.--.', ')': '-.--.-'
}

week_letters = {
    1: 'ETIANM',
    2: 'SURWDK',
    3: 'GOHVFL',
    4: 'PJBXC',
    5: 'YZQ1234567890',
    6: '. , ? /'
}

# === Text-to-Speech (TTS) Function ===
def speak_text(engine, text):
    system = platform.system()
    #print(f"[DEBUG] Speaking ({system}): {text}")
    
    if system == "Darwin":  # macOS
        os.system(f"say '{text.lower()}'")  # Fix: use lowercase to avoid "capital" being spoken
    elif system == "Linux":
        if shutil.which("espeak"):
            subprocess.run(["espeak", text])
    elif system == "Windows":
        if engine:
            try:
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            except Exception as e:
                print(f"[DEBUG] pyttsx3 failed: {e}")

# === Tone Generation ===
def generate_tone(frequency, duration, sample_rate=44100):
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    tone = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
    stereo_tone = np.stack((tone, tone), axis=-1)  # Stereo
    return stereo_tone

# === Play Dot or Dash ===
def play_morse_sound(symbol, frequency):
    duration = dot_duration if symbol == '.' else dot_duration * 3
    sound_array = generate_tone(frequency, duration)
    sound = pygame.sndarray.make_sound(sound_array)
    sound.play()
    pygame.time.delay(int(duration * 1000))  # Wait for sound to finish

# === Utility Functions ===
def print_yellow(text):
    print(f"\033[33m{text}\033[0m")

def print_blue(text):
    print(f"\033[34m{text}\033[0m")

# === Play Letter ===
def play_letter(engine, letter):
    if letter == ' ':
        print("Space (between words)")
        pygame.time.delay(int(dot_duration * 7 * 1000))
        return

    if show_morse:
        print_yellow(f"Sending: {letter} ({morse_code[letter]})")
    else:
        print_yellow(f"Sending: {letter}")

    # Play the morse code for the letter
    for symbol in morse_code[letter]:
        play_morse_sound(symbol, current_frequency)
        pygame.time.delay(int(dot_duration * 1000))

    # Speak the letter
    if voice_enabled and engine:
        # Wait so the user can write their guess.
        pygame.time.delay(int(dot_duration * 6 * 1000))
        speak_text(engine, letter)

    # Space between letters
    pygame.time.delay(int(dot_duration * 3 * 1000))

# === Practice Functions ===
def practice_week_letters_continuously(week_num):
    letters = week_letters[week_num]
    try:
        engine = pyttsx3.init()
    except Exception:
        engine = None
    while True:
        letter = random.choice(letters)
        if letter == ' ':
            continue

        play_letter(engine, letter)


def practice_all_characters_continuously():
    try:
        engine = pyttsx3.init()
    except Exception:
        engine = None

    while True:
        letter = random.choice(list(morse_code.keys()))
        play_letter(engine, letter)

def play_user_text_in_morse(user_text):
    try:
        engine = pyttsx3.init()
    except Exception:
        engine = None

    for char in user_text.upper():
        if char in morse_code or char == ' ':
            play_letter(engine, char)
        else:
            print(f"Skipping unsupported character: {char}")

# === Settings Adjustment ===
def adjust_frequency():
    global current_frequency
    try:
        new_frequency = int(input("Enter new frequency (400-1000 Hz): "))
        if 400 <= new_frequency <= 1000:
            current_frequency = new_frequency
            print(f"Frequency set to {current_frequency} Hz.")
        else:
            print("Invalid frequency.")
    except ValueError:
        print("Invalid input.")

# === Main Menu ===
def show_menu():
    global current_wpm, dot_duration, current_frequency, show_morse, voice_enabled
    while True:
        print_blue("Morse Code Trainer by Glenn Maclean WA7SPY")
        print_blue("Learning method by Michael Aretsky N6MQL (RIP)")
        print_blue("Practice 15 mins/day for 5-6 weeks to learn Morse!")
        print_blue("Use a straight key and oscillator for best results.\n")

        print_blue("1. Week 1: ETIANM")
        print_blue("2. Week 2: SURWDK")
        print_blue("3. Week 3: GOHVFL")
        print_blue("4. Week 4: PJBXC")
        print_blue("5. Week 5: YZQ1234567890")
        print_blue("6. Week 6: . , ? /")
        print_blue("7. All Characters")
        print_blue("8. Enter custom text")
        print_blue("9. Adjust Frequency")
        print_blue("10. Set WPM (Words Per Minute)")
        print_blue("11. Toggle Morse Display")
        print_blue("12. Toggle Voice")
        print_blue("13. Exit")

        print(f"Display: {'ON' if show_morse else 'OFF'} | Voice: {'ON' if voice_enabled else 'OFF'} | WPM: {current_wpm} | Frequency: {current_frequency}Hz")
        choice = input("Enter choice (1-13): ")

        if choice == '1':
            practice_week_letters_continuously(1)
        elif choice == '2':
            practice_week_letters_continuously(2)
        elif choice == '3':
            practice_week_letters_continuously(3)
        elif choice == '4':
            practice_week_letters_continuously(4)
        elif choice == '5':
            practice_week_letters_continuously(5)
        elif choice == '6':
            practice_week_letters_continuously(6)
        elif choice == '7':
            practice_all_characters_continuously()
        elif choice == '8':
            user_text = input("Enter text: ")
            play_user_text_in_morse(user_text)
        elif choice == '9':
            adjust_frequency()
        elif choice == '10':
            try:
                current_wpm = int(input("Enter WPM (5-40): "))
                if 5 <= current_wpm <= 40:
                    dot_duration = 60 / (current_wpm * 50)
                    print(f"WPM set to {current_wpm}")
                else:
                    print("Invalid WPM value.")
            except ValueError:
                print("Invalid input.")
        elif choice == '11':
            show_morse = not show_morse
            print(f"Morse code display is now {'ON' if show_morse else 'OFF'}")
        elif choice == '12':
            voice_enabled = not voice_enabled
            print(f"Voice is now {'ON' if voice_enabled else 'OFF'}")
        elif choice == '13':
            graceful_exit(None, None)
        else:
            print("Invalid choice.")

# === Exit Handler ===
def graceful_exit(signal_received, frame):
    print("\nExiting program. Goodbye!")
    pygame.quit()
    exit(0)

# === Handle Ctrl+C ===
signal.signal(signal.SIGINT, graceful_exit)

# === Run Menu ===
if __name__ == "__main__":
    show_menu()

