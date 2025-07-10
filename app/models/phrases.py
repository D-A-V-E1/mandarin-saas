from pydantic import BaseModel
from typing import List, Optional

class Quiz(BaseModel):
    question: str
    options: List[str]
    answer: str

class Phrase(BaseModel):
    pinyin: str
    translation: str
    audio: str
    category: str
    level: str
    quiz: Optional[Quiz]
    culture: Optional[str]