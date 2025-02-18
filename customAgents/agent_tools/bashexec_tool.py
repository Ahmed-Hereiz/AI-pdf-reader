import os
import subprocess
from typing import Any
from customAgents.agent_tools import BaseTool

class BashRuntimeTool(BaseTool):
    def __init__(
            self,
            description: str = "Tool used to run bash scripts or Linux commands",
            tool_name: str = None
            ):
        
        super().__init__(description, tool_name)

    def execute_func(self, code: str) -> Any:
        return self._execute_bash(code)
    
    def _execute_bash(self, code: str) -> str:
        
        parsed_code = self._parse_code(code)

        with open("tmp_script.sh", "w") as file:
            file.write(parsed_code)
        
        try:
            os.chmod("tmp_script.sh", 0o755)

            result = subprocess.run(
                ["bash", "tmp_script.sh"],
                capture_output=True,
                text=True
            )

            output = result.stdout
            errors = result.stderr

            if errors:
                return f"Output:\n{output}\nErrors:\n{errors}"
            return f"Output:\n{output}"
        
        except subprocess.CalledProcessError as e:
            return f"Errors:\n{e.stderr}\nOutput:\n{e.stdout}"
        finally:
            os.remove("tmp_script.sh")
        
    def _parse_code(self, code: str) -> str:

        if isinstance(code, list):
            code = "\n".join(code)

        code = code.strip()
        
        if code.startswith("```") and code.endswith("```"):
            lines = code.splitlines()
            if lines[0].strip().startswith("```") and lines[-1].strip().startswith("```"):
                code = "\n".join(lines[1:-1])
            else:
                code = code[3:-3].strip()

        if ";" in code:
            code = code.replace(";", "\n")
        
        return str(code)


# Usage :

# tool = BashRuntimeTool()

# code = """
# ```bash
# #!/bin/bash
# echo "Starting process..."
# echo "Listing files in the current directory:"
# ls -l
# echo "hello world"
# ```
# """

# result = tool.execute_func(code)
# print(result)

