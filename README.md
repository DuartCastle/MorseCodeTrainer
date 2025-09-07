# Morse Code Trainer

Created by: WA7SPY

---

## About

This program helps you learn Morse code interactively!

You can:

- Practice letters in weekly groups
- Send random words and sentences built from each week's letters
- Send random call signs, numbers, and punctuation
- Enter your own text to send in Morse code
- **Send the contents of a text file as Morse code** (menu option 9)
- Adjust tone frequency and speed (WPM)
- Use **Farnsworth timing** to slow spacing between letters/words while keeping character speed high
- Stretch spacing further with a **Farnsworth gap multiplier**
- Use Flash Card Mode to display large letters as they are sent
- Toggle dot-dash display for reference
- Toggle voice mode to speak letters aloud

Morse code is an **audible language**—turn off the visual dot-dash display as soon as you can.

**Practice at least 15 minutes per day.**  
Do not move to the next week until you can copy the current week confidently.

**GOOD LUCK—ENJOY LEARNING!**

---

## Revision History

**v2.2 – September 2025**
- Added menu option 9: **Send from a text file**
- Added **Farnsworth timing controls**:
  - Set Farnsworth effective WPM
  - Adjust Farnsworth gap multiplier
- Fixed intra-character spacing (correctly plays “M=--”, “I=..”, etc.)
- Improved macOS audio initialization (CoreAudio)

**v2.1 – July 7, 2025**
- Enter = pause/resume; `q` + Enter = stop and return to menu
- Minor on-screen instruction improvements

---

## Requirements

- Python 3
- [pygame](https://www.pygame.org/)
- numpy

---

## Installation

Follow the steps below for your platform.

---

### Windows

1. Install Python 3 from [python.org](https://www.python.org/).
2. Open **Command Prompt**.
3. Install dependencies:

    ```sh
    pip install pygame numpy
    ```

4. *(Optional)* Create a virtual environment:

    ```sh
    python -m venv pyEnv
    pyEnv\Scripts\activate
    ```

---

### macOS and Linux

1. Make sure Python 3 is installed:

    ```sh
    python3 --version
    ```

2. Install dependencies:

    ```sh
    pip3 install pygame numpy
    ```

3. *(Optional)* Create a virtual environment:

    ```sh
    python3 -m venv pyEnv
    source pyEnv/bin/activate
    ```

---

## Important Files

Make sure the following files are located in the **same folder** before running the program:

- `morsecode.py` – the main program.
- `ascii_letters.py` – provides the large letter display for Flash Card Mode.

If `ascii_letters.py` is missing or not in the same directory as `morsecode.py`, the program will not start and you will see an error similar to:

```
ModuleNotFoundError: No module named 'ascii_letters'
```

---

## Running the Program

Navigate to the folder containing `morsecode.py`.

**Windows:**

```sh
python morsecode.py
```

**macOS and Linux:**

```sh
python3 morsecode.py
```

---

## Example Screen Output

```
Morse Code Trainer - Main Menu
1. Practice Week Letters
2. Random Word
3. Random Sentence
4. Random Call Sign
5. Random Numbers (0123456789)
6. Random Punctuation (.,?/)
7. Enter Custom Text
8. Settings
9. Exit
Press [Enter] to Pause. Press [q] then [Enter] to Stop.
Display: ON | Flash: OFF | WPM: 10 | Frequency: 700Hz
Choice:
```

While sending, the program will display:

```
Sending: E (.)
```

---

## Using the Program

**Main Menu Options:**
- **1. Practice Week Letters:** Sends letters from a specific week's group randomly.
- **2. Random Word:** Sends 3 randomly selected words.
- **3. Random Sentence:** Sends a randomly selected sentence.
- **4. Random Call Sign:** Sends a randomly selected ham call sign.
- **5. Random Numbers:** Sends numbers randomly.
- **6. Random Punctuation:** Sends punctuation marks randomly.
- **7. Enter Custom Text:** You type anything, and it will send it back in Morse code.
- **8. Settings:** Adjust frequency, WPM, display options, and flash card mode.
- **9. Exit:** Close the program.

---

## Pausing and Stopping

- **Pause/Resume sending:**  
  Press **Enter** during playback.
- **Stop sending and return to the main menu:**  
  Press **q** and then **Enter** during playback.
- **Exit completely:**  
  Use **menu option 9**.

---

## Acknowledgment

This program’s method and sequence for learning Morse Code are inspired by the work of **Mike Aretsky, N6MQL**.

Mike was a beloved ham radio leader, Morse code advocate, accomplished engineer, and community pillar. His passions spanned amateur radio, music, electronics, and service—leaving a vibrant legacy respected by many in the Sacramento Valley.

This project is dedicated to his memory and to his commitment to sharing Morse Code with new generations.

---
