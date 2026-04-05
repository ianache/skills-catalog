import os
import yaml
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

class Skill:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.metadata: Dict[str, Any] = {}
        self.instructions: str = ""
        self.tools: List[Dict[str, Any]] = []
        self.scripts_path = path / "scripts"
        self.assets_path = path / "assets"
        self.references_path = path / "references"
        self._load()

    def _load(self):
        # Load SKILL.md
        skill_md_path = self.path / "SKILL.md"
        if skill_md_path.exists():
            content = skill_md_path.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    self.metadata = yaml.safe_load(parts[1])
                    self.instructions = parts[2].strip()
            else:
                self.instructions = content.strip()
        
        # Fallback to instructions.md if instructions are empty
        if not self.instructions:
            instructions_file = self.path / "instructions.md"
            if instructions_file.exists():
                self.instructions = instructions_file.read_text(encoding="utf-8").strip()

        # Load skills.json
        skills_json_path = self.path / "skills.json"
        if skills_json_path.exists():
            try:
                data = json.loads(skills_json_path.read_text(encoding="utf-8"))
                self.tools = data.get("tools", [])
                # Handle different formats (Anthropic input_schema vs OpenAI parameters)
                for tool in self.tools:
                    if "input_schema" in tool and "parameters" not in tool:
                        tool["parameters"] = tool["input_schema"]
            except json.JSONDecodeError:
                print(f"Error decoding {skills_json_path}")

    def __repr__(self):
        return f"Skill(name={self.name}, tools={len(self.tools)})"

def load_skills(skills_dir: str) -> List[Skill]:
    skills = []
    base_path = Path(skills_dir)
    if not base_path.exists():
        return []

    for item in base_path.iterdir():
        if item.is_dir():
            skills.append(Skill(item))
    
    return skills
