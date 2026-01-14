from typing import Dict, Any, Tuple, List
import copy
from .definitions import (
    CommandType, TimelineCommand, CutCommand, SplitCommand, MoveCommand, 
    AddTextCommand, GradeCommand
)

class CommandProcessor:
    @staticmethod
    def apply(project_state: Dict[str, Any], command: TimelineCommand) -> Tuple[Dict[str, Any], TimelineCommand]:
        """
        Applies a command to the project state and returns the new state + inverse command (for undo).
        Does not mutate the input state in-place (returns deep copy).
        """
        new_state = copy.deepcopy(project_state)
        inverse_command = None
        
        if command.type == CommandType.CUT:
            new_state, inverse_command = CommandProcessor._apply_cut(new_state, command)
        elif command.type == CommandType.SPLIT:
            new_state, inverse_command = CommandProcessor._apply_split(new_state, command)
        elif command.type == CommandType.MOVE:
            new_state, inverse_command = CommandProcessor._apply_move(new_state, command)
        elif command.type == CommandType.ADD_TEXT:
            new_state, inverse_command = CommandProcessor._apply_add_text(new_state, command)
        elif command.type == CommandType.GRADE:
            new_state, inverse_command = CommandProcessor._apply_grade(new_state, command)
            
        return new_state, inverse_command

    @staticmethod
    def _get_clips(state: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Handle variations in naming
        return state.get("edl", state.get("clips", []))

    @staticmethod
    def _apply_cut(state: Dict[str, Any], cmd: CutCommand) -> Tuple[Dict[str, Any], CutCommand]:
        clips = CommandProcessor._get_clips(state)
        target = next((c for c in clips if str(c.get("id")) == str(cmd.clip_id)), None)
        
        if not target:
            return state, cmd # No-op
            
        # Determine current Keep status
        # In gravity, 'keep' might be boolean or string "true"/"false"
        # We normalize to boolean logic for toggle
        
        current_keep = str(target.get("keep", "true")).lower() == "true"
        
        new_keep = current_keep
        if cmd.action == "reject":
            new_keep = False
        elif cmd.action == "keep":
            new_keep = True
        elif cmd.action == "toggle":
            new_keep = not current_keep
            
        target["keep"] = new_keep
        
        # Inverse: Set it back to what it was
        inverse_action = "keep" if current_keep else "reject"
        inverse = CutCommand(clip_id=cmd.clip_id, action=inverse_action)
        
        return state, inverse

    @staticmethod
    def _apply_move(state: Dict[str, Any], cmd: MoveCommand) -> Tuple[Dict[str, Any], MoveCommand]:
        clips = CommandProcessor._get_clips(state)
        target = next((c for c in clips if str(c.get("id")) == str(cmd.clip_id)), None)
        
        if not target:
            return state, cmd
            
        old_start = target.get("start", 0.0)
        # old_track = target.get("track", 0) # Not fully supported in simplistic model yet
        
        target["start"] = cmd.new_start_time
        
        inverse = MoveCommand(clip_id=cmd.clip_id, new_start_time=old_start)
        return state, inverse

    @staticmethod
    def _apply_add_text(state: Dict[str, Any], cmd: AddTextCommand) -> Tuple[Dict[str, Any], AddTextCommand]:
        overlays = state.get("overlays", [])
        if "overlays" not in state:
            state["overlays"] = overlays
            
        new_overlay = {
            "id": f"text_{len(overlays) + 1}_{int(cmd.start_time*100)}", # Simple ID gen
            "text": cmd.content,
            "start": cmd.start_time,
            "end": cmd.start_time + cmd.duration,
            "style": cmd.style
        }
        overlays.append(new_overlay)
        
        # Inverse: Remove this specific overlay (By ID logic ideally)
        # For AddText, strict inverse is "Delete Object". 
        # Since we don't have DeleteCommand in simplified list, we mock it via Cut?
        # Or we assume Undo is handled by restoring state snapshot in frontend.
        # But per requirements "Undo = reverse command".
        # We need a DeleteCommand for strict inversion.
        # For now, we return None or a placeholder.
        
        # TODO: Implement RemoveCommand
        return state, None 

    @staticmethod
    def _apply_split(state: Dict[str, Any], cmd: SplitCommand) -> Tuple[Dict[str, Any], SplitCommand]:
        # Split logic is complex (duplicate clip, adjust start/end)
        # Placeholder for now
        return state, None

    @staticmethod
    def _apply_grade(state: Dict[str, Any], cmd: GradeCommand) -> Tuple[Dict[str, Any], GradeCommand]:
        # Apply to global or clip
        if cmd.clip_id:
             clips = CommandProcessor._get_clips(state)
             target = next((c for c in clips if str(c.get("id")) == str(cmd.clip_id)), None)
             if target:
                 # Store old
                 old_grade = target.get("grade", {})
                 new_grade = old_grade.copy()
                 if cmd.brightness is not None: new_grade["brightness"] = cmd.brightness
                 if cmd.contrast is not None: new_grade["contrast"] = cmd.contrast
                 target["grade"] = new_grade
                 # Inverse: Restore old grade
                 # This requires GradeCommand to support setting all props (which it does via Optional)
                 # Simpler to just assume snapshot undo for grade.
                 inverse = GradeCommand(clip_id=cmd.clip_id, **old_grade) # conceptual
                 return state, inverse
        
        return state, None
