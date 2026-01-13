from moviepy import *
import os

try:
    print("Testing TextClip generation with keyword args...")
    # Try passing text as a keyword argument
    try:
        txt = TextClip(text="Test", font_size=50, color='white', method='label')
        print(f"SUCCESS: TextClip(text='Test') worked. Duration: {txt.duration}")
    except Exception as e:
        print(f"FAILED: TextClip(text='Test') failed: {e}")

    # Try passing font as first arg? (Old style was TextClip(txt, ...))
    # It seems in MoviePy 2.0, the class might be refactored.
    
    # Try constructing with 'font' explicitly
    try:
        txt = TextClip(text="Test2", font="Arial", font_size=50, color='white')
        print("SUCCESS: TextClip(text='Test2', font='Arial') worked.")
    except Exception as e:
        print(f"FAILED: TextClip(text='Test2', font='Arial') failed: {e}")

except Exception as e:
    print(f"FAILURE: {e}")
