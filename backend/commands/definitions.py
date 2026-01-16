from enum import Enum
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field

class CommandType(str, Enum):
    CUT = "CUT"
    SPLIT = "SPLIT"
    MOVE = "MOVE"
    ADD_TEXT = "ADD_TEXT"
    GRADE = "GRADE"

class BaseCommand(BaseModel):
    type: CommandType
    timestamp: float = Field(default_factory=lambda: 0.0) # Execution time or creating time

class CutCommand(BaseCommand):
    type: Literal[CommandType.CUT] = CommandType.CUT
    clip_id: str
    action: Literal["keep", "reject", "toggle"] = "reject" 

class SplitCommand(BaseCommand):
    type: Literal[CommandType.SPLIT] = CommandType.SPLIT
    clip_id: str
    split_time: float # Relative to project or clip source? Usually project time for edits.

class MoveCommand(BaseCommand):
    type: Literal[CommandType.MOVE] = CommandType.MOVE
    clip_id: str
    new_start_time: float
    track_index: int = 0

class AddTextCommand(BaseCommand):
    type: Literal[CommandType.ADD_TEXT] = CommandType.ADD_TEXT
    content: str
    start_time: float
    duration: float
    style: str = "pop"
    
class GradeCommand(BaseCommand):
    type: Literal[CommandType.GRADE] = CommandType.GRADE
    clip_id: Optional[str] = None # None = Global
    brightness: Optional[float] = None
    contrast: Optional[float] = None
    saturation: Optional[float] = None
    temperature: Optional[float] = None
    filter_name: Optional[str] = None

# Union for parsing
TimelineCommand = Union[CutCommand, SplitCommand, MoveCommand, AddTextCommand, GradeCommand]
