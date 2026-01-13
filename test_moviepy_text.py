from moviepy import *
import os

try:
    print("Testing TextClip generation...")
    # Try basic text clip with MoviePy 2.x syntax
    txt = TextClip("Test", font_size=50, color='white', method='label')
    print(f"TextClip created: {txt}")
    print(f"Duration: {txt.duration}")
    
    # Try with font
    txt_font = TextClip("Font Test", font_size=50, font='Arial', color='white', method='label')
    print("TextClip with font Arial created.")
    
    print("SUCCESS: TextClip seems to work.")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
