import sys

with open('src/narrative/generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_str = """from typing import Any, Dict
from ..models import CharacterProfile

class LLMNarrativeGenerator:"""

new_str = """from typing import Any, Dict
from ..models import CharacterProfile
from ..interfaces import BaseNarrativeGenerator

class LLMNarrativeGenerator(BaseNarrativeGenerator):"""

content = content.replace(old_str, new_str)

old_str2 = """        return f"# {story_title}\n\n" + "\n\n".join(story_parts)

class NarrativeGenerator:"""

new_str2 = """        return f"# {story_title}\n\n" + "\n\n".join(story_parts)

class NarrativeGenerator(BaseNarrativeGenerator):"""

content = content.replace(old_str2, new_str2)

with open('src/narrative/generator_fixed.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Replaced generator.py logic.')