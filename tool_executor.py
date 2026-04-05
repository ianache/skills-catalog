import os
import subprocess
import importlib.util
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

class ToolExecutor:
    def __init__(self, skills: List[Any]):
        self.tool_map: Dict[str, Dict[str, Any]] = {}
        for skill in skills:
            for tool in skill.tools:
                tool_name = tool["name"]
                # Try to find a script for this tool
                script_path = self._find_script(skill, tool_name)
                if script_path:
                    self.tool_map[tool_name] = {
                        "skill": skill,
                        "script_path": script_path,
                        "tool_def": tool
                    }

    def _find_script(self, skill: Any, tool_name: str) -> Optional[Path]:
        scripts_dir = skill.scripts_path
        if not scripts_dir.exists():
            return None
        
        # Check for .py, .js, .sh
        for ext in [".py", ".js", ".sh"]:
            script_path = scripts_dir / f"{tool_name}{ext}"
            if script_path.exists():
                return script_path
        return None

    def execute(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if tool_name not in self.tool_map:
            raise ValueError(f"Tool {tool_name} not found in registry")
        
        info = self.tool_map[tool_name]
        script_path = info["script_path"]
        
        if script_path.suffix == ".py":
            return self._execute_python(script_path, args)
        elif script_path.suffix == ".js":
            return self._execute_subprocess(["node", str(script_path)], args)
        elif script_path.suffix == ".sh":
            return self._execute_subprocess(["bash", str(script_path)], args)
        else:
            raise ValueError(f"Unsupported script type: {script_path.suffix}")

    def _execute_python(self, script_path: Path, args: Dict[str, Any]) -> Any:
        module_name = script_path.stem
        spec = importlib.util.spec_from_file_location(module_name, str(script_path))
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "execute"):
                return module.execute(**args)
            else:
                raise AttributeError(f"Script {script_path} does not have an 'execute' function")
        raise ImportError(f"Failed to import {script_path}")

    def _execute_subprocess(self, command_base: List[str], args: Dict[str, Any]) -> Any:
        import json
        params_json = json.dumps(args)
        try:
            result = subprocess.run(
                command_base + [params_json],
                capture_output=True,
                text=True,
                check=True
            )
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return {"error": str(e), "stdout": e.stdout, "stderr": e.stderr}
