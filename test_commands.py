import json
import copy
import sys
import os

# Ensure backend matches path
sys.path.append(os.getcwd())

from backend.commands.definitions import CutCommand, AddTextCommand, MoveCommand, GradeCommand
from backend.commands.core import CommandProcessor
from backend.commands.parser import CommandParser

def run_tests():
    print("🚀 Starting Command System Tests...\n")
    
    # --- MOCK STATE ---
    initial_state = {
        "name": "Test Project",
        "edl": [
            {"id": "clip1", "start": 0.0, "end": 10.0, "keep": True},
            {"id": "clip2", "start": 10.0, "end": 20.0, "keep": True}
        ],
        "overlays": []
    }
    
    print(f"Initial State Clips: {len(initial_state['edl'])}")
    print("-" * 40)

    # --- TEST 1: CUT COMMAND (Reject) ---
    print("\n[TEST 1] Cutting 'clip1' (Reject)...")
    cut_cmd = CutCommand(clip_id="clip1", action="reject")
    
    state_v2, inverse_v2 = CommandProcessor.apply(initial_state, cut_cmd)
    
    # Assert
    c1 = next(c for c in state_v2["edl"] if c["id"] == "clip1")
    if c1["keep"] is False:
        print("✅ PASS: Clip1 'keep' is now False.")
    else:
        print(f"❌ FAIL: Clip1 'keep' is {c1['keep']}.")
        
    # --- TEST 1.1: UNDO CUT ---
    print("   [UNDO] Reversing Cut...")
    state_v3, _ = CommandProcessor.apply(state_v2, inverse_v2)
    c1_undo = next(c for c in state_v3["edl"] if c["id"] == "clip1")
    if c1_undo["keep"] is True:
         print("✅ PASS: Clip1 restored to True.")
    else:
         print(f"❌ FAIL: Undo failed. State: {c1_undo['keep']}")


    # --- TEST 2: ADD TEXT ---
    print("\n[TEST 2] Adding Text Overlay...")
    text_cmd = AddTextCommand(content="Hello World", start_time=5.0, duration=3.0)
    
    state_v4, inverse_v4 = CommandProcessor.apply(initial_state, text_cmd) # Apply to fresh state
    
    if len(state_v4["overlays"]) == 1:
        ov = state_v4["overlays"][0]
        if ov["text"] == "Hello World" and ov["start"] == 5.0:
            print("✅ PASS: Overlay added correctly.")
        else:
            print(f"❌ FAIL: Overlay data mismatch: {ov}")
    else:
        print(f"❌ FAIL: Overlay count is {len(state_v4['overlays'])}")


    # --- TEST 3: PARSER ---
    print("\n[TEST 3] Parsing AI Output...")
    ai_text = """
    Sure, I removed the bad clip.
    ```tool_code
    gravity_ai.cut_clip(clip_id="clip2")
    gravity_ai.add_text(content="Epic!", start_time=2.0)
    ```
    """
    
    commands = CommandParser.parse_tool_code(ai_text)
    print(f"   Parsed {len(commands)} commands.")
    
    if len(commands) == 2:
        if isinstance(commands[0], CutCommand) and commands[0].clip_id == "clip2":
            print("✅ PASS: Parsed CutCommand correctly.")
        else:
             print(f"❌ FAIL: Command 0 mismatch: {commands[0]}")
             
        if isinstance(commands[1], AddTextCommand) and commands[1].content == "Epic!":
            print("✅ PASS: Parsed AddTextCommand correctly.")
        else:
             print(f"❌ FAIL: Command 1 mismatch: {commands[1]}")
    else:
        print("❌ FAIL: Did not parse 2 commands.")

    print("\n" + "="*40)
    print("ALL TESTS COMPLETE")

if __name__ == "__main__":
    run_tests()
