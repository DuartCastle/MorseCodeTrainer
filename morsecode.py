import json
import os
import platform
import random
import shutil
import subprocess
import signal

from ascii_letters import ascii_letter

SETTINGS_FILE = "morse_settings.json"

# === 3rd Party Modules ===
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


# === Settings File Functions ===
def load_settings():
    default_settings = {
        "current_frequency": 700,
        "current_wpm": 10,
        "show_morse": True,
        "flash_card_mode_enabled": False,
        "voice_enabled": False
    }
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        for k, v in default_settings.items():
            if k not in settings:
                settings[k] = v
        return settings
    else:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(default_settings, f, indent=2)
        return default_settings

def save_settings():
    settings = {
        "current_frequency": current_frequency,
        "current_wpm": current_wpm,
        "show_morse": show_morse,
        "flash_card_mode_enabled": flash_card_mode_enabled,
        "voice_enabled": voice_enabled
    }
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

# === Initialize Pygame ===
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2)

# === Load Settings ===
settings = load_settings()
current_frequency = settings["current_frequency"]
current_wpm = settings["current_wpm"]
show_morse = settings["show_morse"]
flash_card_mode_enabled = settings["flash_card_mode_enabled"]
voice_enabled = settings["voice_enabled"]
dot_duration = 60.0 / (current_wpm * 50.0)
timeout_supported = True
engine = None

# === Morse Code Letters, Words, Sentences, etc. ===
morse_code = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
    'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
    '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', '/': '-..-.'
}

week_letters = {
    1: 'ETIANM',
    2: 'SURWDK',
    3: 'GOHVFL',
    4: 'PJBXC',
    5: 'YZQ1234567890',
    6: '.,?/',
    7: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890.,?/',
    8: '0123456789',
    9: '.,?/'
}

additional_characters = {
    1: "",
    2: "",
    3: "",
    4: "",
    5: "",
    6: "",
    7: "",
}

week1_words = ["MAN", "TEN", "TAME", "MEAT", "TEAM", "MINE", "AMEN", "ANTI", "ITEM"]
week1_sentences = ["A MAN MET ME", "AN ANT ATE ME", "I AM IN A TENT"]

week12_words = ["WIND", "MASK", "TANK", "STRAW", "MURDER", "WARM", "SAND", "DARK", "UNDER", "SWIM"]
week12_sentences = ["I SAW A DARK WIND", "WE MUST STAND", "MARK WENT UNDER"]

week123_words = ["FARM", "GLOVE", "WOLF", "SHADOW", "GHOST", "DISH", "NORTH", "LADDER", "FLASH", "FORK"]
week123_sentences = ["GO HUNT FOR A SHADOW", "THE WOLF MOVES FAST", "HIS FARM HAD A LADDER"]

week1234_words = ["BLOCK", "JUMP", "CAMP", "PACK", "BRICK", "JAW", "SCRUB", "DUMP", "BACKUP", "SCARF"]
week1234_sentences = ["PACK A BACKUP FOR CAMP", "THE BRICK WALL WAS SCRUBBED", "JUMP INTO THE DARK CAMP"]

week7_words = ["BROWN", "JUMPS", "LAZY", "DOG", "FOX", "OVER", "QUICK", "THE", "ZEBRA", "PACK", "VEX", "JOKES", "QUIZ"]
week7_sentences = ["THE QUICK BROWN FOX JUMPS OVER LAZY DOG.", "PACK MY BOX WITH FIVE DOZEN LIQUOR JUGS."]

all_words = week1_words + week12_words + week123_words + week1234_words

call_signs = ["WA7SPY/QRP", "KB1FJZ", "N8FIT", "KA2UTL", "W4ZX", "N3BKQ", "WA5PRY/M", "N6OQN", "W8GSH"]

# === Utility Functions ===
def prompt_for_pause(duration_seconds=3.0) -> str:
    """Wait for specified duration, but allow Enter to pause"""
    global timeout_supported
    # If timeout is not supported, just wait for the duration.
    if timeout_supported != True:
        pygame.time.wait(int(duration_seconds * 1000))
        return 'continue'

    # If timeout is supported, wait for input with specified timeout.
    try:
        import select
        import sys

        # Wait for input with specified timeout
        if select.select([sys.stdin], [], [], duration_seconds)[0]:
            user_input = input().strip().lower()
            if user_input == 'q':
                return 'quit'
            elif user_input == "":
                print_blue("PAUSED - Press Enter to continue, or type 'q' to quit...")
                user_input = input().strip().lower()
                if user_input == 'q':
                    return 'quit'
                else:
                    print_blue("RESUMED")
                    return 'continue'
        else:
            # Timeout occurred, continue automatically
            return 'continue'
    except:
        # Fallback for systems where select doesn't work
        try:
            import msvcrt  # Windows
            import time

            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\r':  # Enter key
                        print_blue("PAUSED - Press Enter to continue, or type 'q' to quit...")
                        user_input = input().strip().lower()
                        if user_input == 'q':
                            return 'quit'
                        else:
                            print_blue("RESUMED")
                            return 'continue'
                    elif key == b'q':
                        return 'quit'
                time.sleep(0.1)

            # Timeout occurred, continue automatically
            return 'continue'
        except:
            # If we try to use timeout and it fails, don't try again.
            timeout_supported = False
            print_blue("Press Enter to continue, or type 'q' to quit...")
            user_input = input().strip().lower()
            if user_input == 'q':
                return 'quit'
            return 'continue'

def print_blue(text):
    print(f"\033[97m{text}\033[0m")

# === Morse Code Sounds ===
def generate_tone(frequency, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    waveform = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
    return np.column_stack((waveform, waveform))

def play_morse(letter) -> str:
    if letter == ' ':
        result = prompt_for_pause(dot_duration * 7)
        if result == 'quit':
            return 'quit'
        return 'continue'

    for symbol in morse_code.get(letter, ''):
        duration = dot_duration if symbol == '.' else dot_duration * 3
        tone = generate_tone(current_frequency, duration)
        sound = pygame.sndarray.make_sound(tone)
        sound.play()
        
        # Wait for tone duration
        result = prompt_for_pause(duration)
        if result == 'quit':
            return 'quit'
        
        # Wait for element spacing
        result = prompt_for_pause(dot_duration)
        if result == 'quit':
            return 'quit'
    
    # Wait for letter spacing
    result = prompt_for_pause(dot_duration * 3)
    if result == 'quit':
        return 'quit'
    
    return 'continue'

# === Voice ===
def speak_text(text) -> None:
    system = platform.system()
    
    if system == "Darwin":  # macOS
          # Use lowercase to avoid "capital" being spoken
        os.system(f"say '{text.lower()}'")
    elif system == "Linux":
        if shutil.which("espeak"):
            subprocess.run(["espeak", text])
    elif system == "Windows":
        global engine
        if engine:
            try:
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            except Exception as e:
                print(f"[DEBUG] pyttsx3 failed: {e}")

# === Play Letter ===
def play_letter(letter) -> str:
    if letter == ' ':
        print("Space (between words)")
        return prompt_for_pause(dot_duration * 7)

    if flash_card_mode_enabled:
        print("\n\n")
        print_blue(ascii_letter(letter))
    elif show_morse:
        print_blue(f"Sending: {letter} ({morse_code[letter]})")
    else:
        print_blue(f"Sending: {letter}")

    # Play the morse code for the letter
    result = play_morse(letter)
    if result == 'quit':
        return 'quit'

    # Speak the letter
    if voice_enabled:
        # Wait so the user can write their guess.
        result = prompt_for_pause(dot_duration * 6)
        if result == 'quit':
            return 'quit'
        speak_text(letter)

    # Space between letters
    return prompt_for_pause(int(dot_duration * 3))

# === Morse Features ===
def play_text(text) -> str:
    for char in text.upper():
        if char in morse_code or char == ' ':
            result = play_letter(char)
            if result == 'quit':
                return 'quit'
    return 'continue'

def practice_week_letters_continuously(week_num) -> str:
    letters = week_letters[week_num]

    i = 0
    while True:
        letter = random.choice(letters)
        if letter == ' ':
            continue

        # After 5 letters, play a space.
        if i >= 5:
            result = play_letter(' ')
            if result == 'quit':
                break
            i = 0

        result = play_letter(letter)
        if result == 'quit':
            break
        i += 1

def play_random_text(text_list, count=1) -> str:
    # Text is words or sentences.
    if count > 1:
        selection = random.sample(text_list, count)
        text = " ".join(selection)
    else:
        text = random.choice(text_list)
    # Either it completes or they quit. We handle both the same.
    play_text(text)

# === Setting modifications ===
def adjust_frequency():
    global current_frequency
    try:
        new_frequency = int(input("Enter new frequency (400-1000 Hz): "))
        if 400 <= new_frequency <= 1000:
            current_frequency = new_frequency
            save_settings()
            print(f"Frequency set to {current_frequency} Hz.")
        else:
            print("Invalid frequency.")
    except ValueError:
        print("Invalid input.")

# === Menus ===
def settings_menu():
    global current_wpm, dot_duration, show_morse, flash_card_mode_enabled, voice_enabled
    while True:
        print_blue("\nSettings Menu")
        print_blue("0. Return to Main Menu")
        print_blue("1. Adjust Frequency")
        print_blue("2. Set WPM")
        print_blue("3. Toggle Morse Display")
        print_blue("4. Toggle Flash Card Mode")
        print_blue("5. Toggle Voice Mode")
        choice = input("Choice: ").lower()

        if choice == '1':
            adjust_frequency()
        elif choice == '2':
            try:
                current_wpm = int(input("Enter WPM (5-40): "))
                if 5 <= current_wpm <= 40:
                    dot_duration = 60.0 / (current_wpm * 50.0)
                    save_settings()
                    print(f"WPM set to {current_wpm}")
                else:
                    print("Invalid WPM.")
            except ValueError:
                print("Invalid input.")
        elif choice == '3':
            show_morse = not show_morse
            save_settings()
            print(f"Morse display is now {'ON' if show_morse else 'OFF'}")
        elif choice == '4':
            flash_card_mode_enabled = not flash_card_mode_enabled
            show_morse = False
            save_settings()
            print(f"Flash Card Mode is now {'ON' if flash_card_mode_enabled else 'OFF'}")
        elif choice == '5':
            voice_enabled = not voice_enabled
            save_settings()
            print(f"Voice Mode is now {'ON' if voice_enabled else 'OFF'}")
        elif choice == '0':
            break
        else:
            print("Invalid choice.")

def practice_week_menu():
    print_blue("\nPractice Week Letters")
    print_blue("0. Return to Main Menu")
    for i in range(1, 8):
        letters = week_letters[i]
        if i in [1, 2, 3, 4]:
            display = letters
        else:
            display = ''.join(sorted(set(letters)))
        print_blue(f"{i}. Week {i} ({display})")
    choice = input("Choice: ").lower()
    if choice == '0':
        return
    elif choice in [str(i) for i in range(1, 8)]:
        practice_week_letters_continuously(int(choice))
    else:
        print("Invalid choice.")

def random_word_menu():
    print_blue("\nRandom Word Menu")
    print_blue("0. Return to Main Menu")
    print_blue("1. Week 1 Words: " + ", ".join(week1_words))
    print_blue("2. Weeks 1+2 Words: " + ", ".join(week12_words))
    print_blue("3. Weeks 1–3 Words: " + ", ".join(week123_words))
    print_blue("4. Weeks 1–4 Words: " + ", ".join(week1234_words))
    print_blue("5. All Words: " + ", ".join(all_words))
    choice = input("Choice: ").lower()
    if choice == '0':
        return
    elif choice == '1':
        play_random_text(week1_words, count=3)
    elif choice == '2':
        play_random_text(week12_words, count=3)
    elif choice == '3':
        play_random_text(week123_words, count=3)
    elif choice == '4':
        play_random_text(week1234_words, count=3)
    elif choice == '5':
        play_random_text(all_words, count=3)
    else:
        print("Invalid choice.")

def random_sentence_menu():
    print_blue("\nRandom Sentence Menu")
    print_blue("0. Return to Main Menu")
    print_blue("1. Week 1 Sentences: " + "; ".join(week1_sentences))
    print_blue("2. Weeks 1+2 Sentences: " + "; ".join(week12_sentences))
    print_blue("3. Weeks 1–3 Sentences: " + "; ".join(week123_sentences))
    print_blue("4. Weeks 1–4 Sentences: " + "; ".join(week1234_sentences))
    print_blue("5. Week 7 Sentences: " + "; ".join(week7_sentences))
    choice = input("Choice: ").lower()
    if choice == '0':
        return
    elif choice == '1':
        play_random_text(week1_sentences)
    elif choice == '2':
        play_random_text(week12_sentences)
    elif choice == '3':
        play_random_text(week123_sentences)
    elif choice == '4':
        play_random_text(week1234_sentences)
    elif choice == '5':
        play_random_text(week7_sentences)
    else:
        print("Invalid choice.")

def show_main_menu():
    while True:
        print_blue("\n --------------------------------")
        print_blue("| Morse Code Trainer - Main Menu |")
        print_blue(" --------------------------------")
        print_blue("0. Exit")
        print_blue("1. Practice Week Letters")
        print_blue("2. Random Word")
        print_blue("3. Random Sentence")
        print_blue("4. Random Call Sign")
        print_blue("5. Random Numbers (" + week_letters[8] + ")")
        print_blue("6. Random Punctuation (" + week_letters[9] + ")")
        print_blue("7. Enter Custom Text")
        print_blue("8. Settings")
        if timeout_supported == True:
            print(f"\nPress [Enter] to Pause. Press [q] then [Enter] to Stop.")
        print(f"\nDisplay: {'ON' if show_morse else 'OFF'} | Flash: {'ON' if flash_card_mode_enabled else 'OFF'} | Voice: {'ON' if voice_enabled else 'OFF'} | WPM: {current_wpm} | Frequency: {current_frequency}Hz")
        choice = input("Choice: ").lower()

        if choice == '1':
            practice_week_menu()
        elif choice == '2':
            random_word_menu()
        elif choice == '3':
            random_sentence_menu()
        elif choice == '4':
            play_random_text(call_signs)
        elif choice == '5':
            practice_week_letters_continuously(8)
        elif choice == '6':
            practice_week_letters_continuously(9)
        elif choice == '7':
            text = input("Enter custom text: ")
            play_text(text)
        elif choice == '8':
            settings_menu()
        elif choice == '0':
            print("Goodbye!")
            pygame.quit()
            break
        else:
            print("Invalid choice.")

# === Main Program ===
if __name__ == "__main__":
    show_main_menu()
