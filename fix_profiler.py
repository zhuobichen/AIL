import sys

with open('src/character/profiler.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_str = """import json
from typing import Any, Dict
from ..models import CharacterProfile, Relation

class LLMCharacterProfiler:"""

new_str = """import json
from typing import Any, Dict
from ..models import CharacterProfile, Relation
from ..interfaces import BaseCharacterProfiler

class LLMCharacterProfiler(BaseCharacterProfiler):"""

content = content.replace(old_str, new_str)

old_str2 = """        return profiles

class CharacterProfiler:"""

new_str2 = """        return profiles

class CharacterProfiler(BaseCharacterProfiler):"""

content = content.replace(old_str2, new_str2)

with open('src/character/profiler_fixed.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Replaced profiler.py logic.')