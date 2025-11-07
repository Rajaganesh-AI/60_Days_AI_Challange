"""
whatsapp_send_group.py

Opens WhatsApp Web, searches for a group by name, and sends a message.
Uses keyboard shortcuts (Ctrl/Cmd+K to search chats on WhatsApp Web).
"""

import time
import sys
import webbrowser
import pyautogui
import pyperclip
import platform

# ==========================
# CONFIG
# ==========================
GROUP_NAME = "SE - AI-B3 - 2"   # <-- change to your group's exact name
MESSAGE = "Hello everyone! One week Completed! This is an automated message sent via PyAutoGUI.\nHave a nice day!"  # supports newlines
BROWSER_URL = "https://web.whatsapp.com/"
OPEN_BROWSER = True   # set False if you already have WhatsApp Web open and focused
WAIT_FOR_WHATSAPP = 30.0   # seconds to wait for WhatsApp Web to load (increase if slow network)
PAUSE_BETWEEN_ACTIONS = 0.3  # pyautogui pause between actions
# ==========================

pyautogui.PAUSE = PAUSE_BETWEEN_ACTIONS
pyautogui.FAILSAFE = True   # move mouse to upper-left to abort

def is_mac():
    return platform.system().lower() == "darwin"

def shortcut_key(*keys):
    """Return correct key for copy/paste/search depending on platform."""
    # for pyautogui.hotkey we will pass keys directly; use 'command' on mac
    return keys

def paste_text(text):
    """
    Use system clipboard paste because pyautogui.typewrite can be slow and fail with special chars.
    Uses Ctrl+V on Windows/Linux, Cmd+V on macOS.
    """
    pyperclip.copy(text)
    if is_mac():
        pyautogui.hotkey("command", "v")
    else:
        pyautogui.hotkey("ctrl", "v")

def main():
    try:
        # 1) Open WhatsApp Web (if requested)
        if OPEN_BROWSER:
            print("Opening WhatsApp Web in default browser...")
            webbrowser.open(BROWSER_URL)
        else:
            print("Assuming WhatsApp Web is already open and focused.")

        # 2) Wait for WhatsApp Web to load
        print(f"Waiting {WAIT_FOR_WHATSAPP} seconds for WhatsApp Web to load / for you to log in (if needed)...")
        time.sleep(WAIT_FOR_WHATSAPP)

        # 3) Focus search (Ctrl/Cmd+K opens search box in WhatsApp Web)
        print("Opening chat search box (Ctrl/Cmd+K)...")
        
        ##if is_mac():
          ##  pyautogui.hotkey("command", "k")
        ##else:
          ##  pyautogui.hotkey("ctrl", "k")
        ##time.sleep(0.6)
        pyautogui.click(136,209)

        # 4) Type (or paste) group name and press Enter to open the chat
        print(f"Searching for group: {GROUP_NAME!r}")
        paste_text(GROUP_NAME)
        time.sleep(0.6)
        pyautogui.press("enter")
        # small wait for chat to open
        time.sleep(1.2)

        # 5) Paste the message into the message box. Use Shift+Enter for newlines if necessary.
        print("Pasting message into chat...")
        paste_text(MESSAGE)
        time.sleep(0.4)

        # 6) Press Enter to send
        print("Sending message...")
        pyautogui.press("enter")

        print("Message sent successfully!")

    except pyautogui.FailSafeException:
        print("Aborted by moving mouse to a corner (pyautogui.FAILSAFE triggered).")
    except Exception as e:
        print("An error occurred:", type(e).__name__, e)

if __name__ == "__main__":
    main()
