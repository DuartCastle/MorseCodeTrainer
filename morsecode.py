import json
import os
import platform
import random
import shutil
import subprocess
import signal
from typing import Optional

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
        "current_frequency": 500,         # Hz
        "current_wpm": 25,                # character (dot) speed
        "farnsworth_wpm": 5.0,            # effective speed via spacing
        "farnsworth_gap_mult": 2.0,       # extra stretch for inter-char/word
        "show_morse": False,
        "flash_card_mode_enabled": True,
        "voice_enabled": False
    }
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
    else:
        settings = {}

    # Ensure all keys exist (backward compatible)
    for k, v in default_settings.items():
        settings.setdefault(k, v)

    # Write back if we added anything
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)
    return settings


def save_settings():
    settings = {
        "current_frequency": current_frequency,
        "current_wpm": current_wpm,
        "farnsworth_wpm": farnsworth_wpm,
        "farnsworth_gap_mult": farnsworth_gap_mult,
        "show_morse": show_morse,
        "flash_card_mode_enabled": flash_card_mode_enabled,
        "voice_enabled": voice_enabled
    }
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)


# === Robust Pygame init (CoreAudio on macOS) ===
def init_audio():
    system = platform.system()
    if system == "Darwin":
        os.environ["SDL_AUDIODRIVER"] = "coreaudio"
    elif system == "Windows":
        os.environ["SDL_AUDIODRIVER"] = "directsound"
    else:
        os.environ.setdefault("SDL_AUDIODRIVER", "alsa")
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    try:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=1024)
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=1024)
    except pygame.error as e:
        print(f"Audio init error with driver '{os.environ.get('SDL_AUDIODRIVER')}': {e}")
        print("Retrying with SDL default...")
        try:
            os.environ.pop("SDL_AUDIODRIVER", None)
            pygame.mixer.quit(); pygame.quit()
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=1024)
            pygame.init()
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=1024)
        except pygame.error as e2:
            print(f"Default driver failed: {e2}")
            print("Falling back to 'dummy' (no-sound) so timing still runs.")
            os.environ["SDL_AUDIODRIVER"] = "dummy"
            pygame.mixer.quit(); pygame.quit()
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=1024)
            pygame.init()
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=1024)


init_audio()


# === Load Settings ===
settings = load_settings()
current_frequency        = settings["current_frequency"]
current_wpm              = settings["current_wpm"]           # character speed
farnsworth_wpm           = settings["farnsworth_wpm"]        # effective speed
farnsworth_gap_mult      = settings["farnsworth_gap_mult"]   # extra stretch
show_morse               = settings["show_morse"]
flash_card_mode_enabled  = settings["flash_card_mode_enabled"]
voice_enabled            = settings["voice_enabled"]
timeout_supported = True


# === Morse Code Map ===
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

week1_words = ["MAN", "TEN", "TAME", "MEAT", "TEAM", "MINE", "AMEN", "ANTI", "ITEM"]
week1_sentences = ["A MAN MET ME", "AN ANT ATE ME", "I AM IN A TENT"]

week12_words = ["WIND", "MASK", "TANK", "STRAW", "MURDER", "WARM", "SAND", "DARK", "UNDER", "SWIM"]
week12_sentences = ["I SAW A DARK WIND", "WE MUST STAND", "MARK WENT UNDER"]

week123_words = ["FARM", "GLOVE", "WOLF", "SHADOW", "GHOST", "DISH", "NORTH", "LADDER", "FLASH", "FORK"]
week123_sentences = ["GO HUNT FOR A SHADOW", "THE WOLF MOVES FAST", "HIS FARM HAD A LADDER"]

week1234_words = ["BLOCK", "JUMP", "CAMP", "PACK", "BRICK", "JAW", "SCRUB", "DUMP", "BACKUP", "SCARF"]
week1234_sentences = ["PACK A BACKUP FOR CAMP", "THE BRICK WALL WAS SCRUBBED", "JUMP INTO THE DARK CAMP"]

week7_words = ["THE", "QUICK", "BROWN", "FOX", "JUMPS", "OVER", "LAZY", "DOG", "PACK", "MY", "BOX", "WITH", "FIVE", "DOZEN", "LIQUOR", "JUGS"]
week7_sentences = ["THE QUICK BROWN FOX JUMPS OVER LAZY DOG.", "PACK MY BOX WITH FIVE DOZEN LIQUOR JUGS."]

all_words = week1_words + week12_words + week123_words + week1234_words
call_signs = ["WA7SPY/QRP", "KB1FJZ", "N8FIT", "KA2UTL", "W4ZX", "N3BKQ", "WA5PRY/M", "N6OQN", "W8GSH"]


# === Timing helpers (Farnsworth) ===
def dot_duration_seconds(char_wpm: float) -> float:
    # Standard: 1 dot = 1.2 / WPM seconds
    return 1.2 / float(char_wpm)

def farnsworth_scale(char_wpm: float, eff_wpm: float) -> float:
    eff_wpm = max(1e-6, eff_wpm)
    return max(1.0, float(char_wpm) / float(eff_wpm))

def space_durations(char_wpm: float, eff_wpm: float, mult: float):
    d = dot_duration_seconds(char_wpm)
    scale = farnsworth_scale(char_wpm, eff_wpm) * max(0.1, float(mult))
    intra = d * 1.0              # 1 dot between elements (fixed)
    inter_char = d * 3.0 * scale # 3 dots * scale
    inter_word = d * 7.0 * scale # 7 dots * scale
    return d, intra, inter_char, inter_word

def timing_now():
    return space_durations(current_wpm, farnsworth_wpm, farnsworth_gap_mult)


# === Utility Functions ===
def prompt_for_pause(duration_seconds=3.0) -> str:
    """Wait for specified duration, but allow Enter to pause or 'q' to quit."""
    global timeout_supported
    if timeout_supported != True:
        pygame.time.wait(int(duration_seconds * 1000))
        return 'continue'
    try:
        import select, sys
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
            return 'continue'
    except:
        try:
            import msvcrt, time
            start = time.time()
            while time.time() - start < duration_seconds:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\r':
                        print_blue("PAUSED - Press Enter to continue, or type 'q' to quit...")
                        user_input = input().strip().lower()
                        if user_input == 'q':
                            return 'quit'
                        else:
                            print_blue("RESUMED")
                            return 'continue'
                    elif key == b'q':
                        return 'quit'
                time.sleep(0.05)
            return 'continue'
        except:
            timeout_supported = False
            print_blue("Press Enter to continue, or type 'q' to quit...")
            user_input = input().strip().lower()
            if user_input == 'q':
                return 'quit'
            return 'continue'

def print_blue(text):
    print(f"\033[97m{text}\033[0m")


# === Tone generation (mono int16) ===
def generate_tone(frequency, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    # 5 ms ramp to avoid key clicks
    ramp_len = max(1, int(0.005 * sample_rate))
    ramp = np.linspace(0.0, 1.0, ramp_len, dtype=np.float32)
    wave[:ramp_len] *= ramp
    wave[-ramp_len:] *= ramp[::-1]
    wave_int16 = np.int16(wave * 32767)
    return wave_int16  # 1-D mono


# === Core playback (fixed intra-character spacing + Farnsworth) ===
def play_morse(letter) -> str:
    """Play the elements of one character with proper 1-dot gaps BETWEEN elements only."""
    if letter == ' ':
        return 'continue'

    code = morse_code.get(letter, '')
    dot_s, intra_gap, _, _ = timing_now()

    for i, symbol in enumerate(code):
        dur = dot_s * (3.0 if symbol == '-' else 1.0)
        tone = generate_tone(current_frequency, dur)
        sound = pygame.sndarray.make_sound(tone)
        sound.play()

        result = prompt_for_pause(dur)
        if result == 'quit':
            return 'quit'

        # 1 dot gap only if NOT the last element
        if i < len(code) - 1:
            result = prompt_for_pause(intra_gap)
            if result == 'quit':
                return 'quit'

    return 'continue'


# === Voice ===
def speak_text(text) -> None:
    system = platform.system()
    if system == "Darwin":  # macOS
        os.system(f"say '{text.lower()}'")
    elif system == "Linux":
        if shutil.which("espeak"):
            subprocess.run(["espeak", text])
    elif system == "Windows" and pyttsx3 is not None:
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception:
            pass


# === Play Letter ===
def play_letter(letter) -> str:
    dot_s, _, inter_char_gap, inter_word_gap = timing_now()

    if letter == ' ':
        return prompt_for_pause(inter_word_gap)

    if flash_card_mode_enabled:
        print("\n\n")
        print_blue(ascii_letter(letter))
    elif show_morse:
        print_blue(f"Sending: {letter} ({morse_code[letter]})")
    else:
        print_blue(f"Sending: {letter}")

    # Play elements
    result = play_morse(letter)
    if result == 'quit':
        return 'quit'

    # Optional voice reveal
    if voice_enabled:
        result = prompt_for_pause(dot_s * 6)
        if result == 'quit':
            return 'quit'
        speak_text(letter)

    # Inter-character spacing ONCE here
    return prompt_for_pause(inter_char_gap)


# === High-level send ===
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
    if count > 1:
        selection = random.sample(text_list, min(count, len(text_list)))
        text = " ".join(selection)
    else:
        text = random.choice(text_list)
    play_text(text)


# === File utilities (NEW) ===
def resolve_path(p: str) -> str:
    """Expand ~ and env vars; return absolute path."""
    p = os.path.expanduser(os.path.expandvars(p.strip()))
    if not os.path.isabs(p):
        p = os.path.abspath(p)
    return p

def load_text_file(p: str) -> Optional[str]:
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        print_blue(f"File error: {e}")
        return None


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


# === Menus (original layout + new file option) ===
def settings_menu():
    global current_wpm, farnsworth_wpm, farnsworth_gap_mult
    global show_morse, flash_card_mode_enabled, voice_enabled

    while True:
        print_blue("\nSettings Menu")
        print_blue("0. Return to Main Menu")
        print_blue("1. Adjust Frequency")
        print_blue(f"2. Set WPM (character/dot speed) [current: {current_wpm}]")
        print_blue(f"3. Toggle Morse Display (currently {'ON' if show_morse else 'OFF'})")
        print_blue(f"4. Toggle Flash Card Mode (currently {'ON' if flash_card_mode_enabled else 'OFF'})")
        print_blue(f"5. Toggle Voice Mode (currently {'ON' if voice_enabled else 'OFF'})")
        print_blue(f"6. Set Farnsworth WPM (effective) [current: {farnsworth_wpm}]")
        print_blue(f"7. Set Farnsworth gap multiplier (0.5–5.0) [current: {farnsworth_gap_mult:.2f}]")
        choice = input("Choice: ").strip().lower()

        if choice == '1':
            adjust_frequency()

        elif choice == '2':
            try:
                w = int(input("Enter Character WPM (5–60): ").strip())
                if 5 <= w <= 60:
                    current_wpm = w
                    save_settings()
                    print(f"Character WPM set to {current_wpm}")
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
            if flash_card_mode_enabled:
                show_morse = False
            save_settings()
            print(f"Flash Card Mode is now {'ON' if flash_card_mode_enabled else 'OFF'}")

        elif choice == '5':
            voice_enabled = not voice_enabled
            save_settings()
            print(f"Voice Mode is now {'ON' if voice_enabled else 'OFF'}")

        elif choice == '6':
            try:
                fw = float(input("Enter Farnsworth WPM (effective, 2–40): ").strip())
                if 2.0 <= fw <= 40.0:
                    farnsworth_wpm = fw
                    save_settings()
                    print(f"Farnsworth WPM set to {farnsworth_wpm}")
                else:
                    print("Invalid Farnsworth WPM.")
            except ValueError:
                print("Invalid input.")

        elif choice == '7':
            try:
                m = float(input("Farnsworth gap multiplier (0.5–5.0): ").strip())
                if 0.5 <= m <= 5.0:
                    farnsworth_gap_mult = m
                    save_settings()
                    print(f"Farnsworth gap multiplier set to {farnsworth_gap_mult:.2f}")
                else:
                    print("Invalid multiplier.")
            except ValueError:
                print("Invalid input.")

        elif choice == '0':
            break

        else:
            print("Invalid choice.")


def practice_week_menu():
    print_blue("\nPractice Week Letters")
    print_blue("0. Return to Main Menu")
    for i in range(1, 8):
        letters = week_letters[i]
        display = letters if i in [1, 2, 3, 4] else ''.join(sorted(set(letters)))
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
        print_blue("9. Send from a text file")  # NEW option

        dot_s, _, inter_char_gap, inter_word_gap = timing_now()
        print(f"\nPress [Enter] to Pause. Press [q] then [Enter] to Stop.")
        print(f"\nDisplay: {'ON' if show_morse else 'OFF'} | Flash: {'ON' if flash_card_mode_enabled else 'OFF'} | Voice: {'ON' if voice_enabled else 'OFF'}"
              f" | WPM: {current_wpm} | Farnsworth: {farnsworth_wpm} | GapMult: {farnsworth_gap_mult:.2f} | Frequency: {current_frequency}Hz")

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
        elif choice == '9':  # NEW
            p = input("Enter path to text file (e.g., ~/Desktop/qso.txt): ").strip()
            rp = resolve_path(p)
            txt = load_text_file(rp)
            if txt is None:
                print_blue("Could not read file. Double-check the full path.")
            else:
                # Normalize whitespace: collapse runs of whitespace to single spaces
                cleaned = ' '.join(txt.split())
                print_blue(f"\nSending file: {rp}\n")
                play_text(cleaned)
        elif choice == '0':
            print("Goodbye!")
            try:
                pygame.mixer.quit()
            except Exception:
                pass
            pygame.quit()
            break
        else:
            print("Invalid choice.")

# === Main Program ===
if __name__ == "__main__":
    show_main_menu()
