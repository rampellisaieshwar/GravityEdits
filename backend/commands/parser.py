import re
import ast
from typing import List, Optional
from .definitions import TimelineCommand, CutCommand, SplitCommand, MoveCommand, AddTextCommand, CommandType

class CommandParser:
    @staticmethod
    def parse_tool_code(text: str) -> List[TimelineCommand]:
        """
        Parses a text containing 'tool_code' blocks or gravity_ai calls into Command Objects.
        """
        commands = []
        
        # Regex to capture gravity_ai.method(kwargs)
        # simplistic parsing handling common patterns
        # We look for lines starting with gravity_ai.
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("gravity_ai."):
                try:
                    # Extract method name
                    func_part = line.split("gravity_ai.")[1].split("(")[0]
                    # Extract args part
                    args_part = line.split("(", 1)[1].rsplit(")", 1)[0]
                    
                    # Safe eval of args using ast.literal_eval for kwargs-like structure?
                    # Python's ast.parse can handle function calls
                    # We'll construct a dummy call "f(args)" and parse it
                    tree = ast.parse(f"f({args_part})")
                    call = tree.body[0].value
                    
                    kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in call.keywords}
                    
                    cmd = CommandParser._map_func_to_command(func_part, kwargs)
                    if cmd:
                        commands.append(cmd)
                        
                except Exception as e:
                    print(f"Failed to parse command line: {line} -> {e}")
                    continue
                    
        return commands

    @staticmethod
    def _map_func_to_command(func_name: str, kwargs: dict) -> Optional[TimelineCommand]:
        if func_name == "cut_clip":
            return CutCommand(
                clip_id=str(kwargs.get("clip_id")),
                action="reject" # Default to reject if just called
            )
        elif func_name == "keep_clip":
            return CutCommand(
                clip_id=str(kwargs.get("clip_id")),
                action="keep"
            )
        elif func_name == "split_clip":
            return SplitCommand(
                clip_id=str(kwargs.get("clip_id")),
                split_time=float(kwargs.get("time", 0))
            )
        elif func_name == "add_text":
            return AddTextCommand(
                content=kwargs.get("content", ""),
                start_time=float(kwargs.get("start_time", 0)),
                duration=float(kwargs.get("duration", 2.0)),
                style=kwargs.get("style", "pop")
            )
        # Expand for others
        return None
