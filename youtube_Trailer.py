import pyautogui
import time
import webbrowser

# --- Step 1: Open YouTube ---
webbrowser.open("https://www.youtube.com")
time.sleep(6)  # wait for the browser to open and page to load

# --- Step 2: Click on YouTube search bar ---
# Adjust coordinates for your screen.
# To find them, run: pyautogui.displayMousePosition() in a terminal
search_bar_x, search_bar_y = 500, 130  # Example coordinates
pyautogui.click(search_bar_x, search_bar_y)
time.sleep(5)

# --- Step 3: Type the search query ---
query = "Bison kaalamadan tamil movie trailer"
pyautogui.typewrite(query, interval=0.1)
time.sleep(1)
pyautogui.press("enter")
time.sleep(6)  # Wait for search results page to load

# --- Step 4: Click on the first video ---
# Again, adjust these coordinates for your screen.
first_video_x, first_video_y = 400, 350  # Example coordinates
pyautogui.click(first_video_x, first_video_y)

print("✅ Script completed: Playing 'Bison kaalamadan tamil movie trailer' on YouTube.")
