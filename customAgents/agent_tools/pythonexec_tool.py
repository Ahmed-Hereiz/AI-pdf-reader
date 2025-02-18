import os
import subprocess
from typing import Any
from customAgents.agent_tools import BaseTool

class PythonRuntimeTool(BaseTool):
    def __init__(
            self,
            description: str = "Tool used to run python code",
            tool_name: str = None
            ):
        
        super().__init__(description, tool_name)

    def execute_func(self, code: str) -> Any:
        return self._execute_code(code)
    
    def _execute_code(self, code: str) -> str:
        
        parsed_code = self._parse_code(code)

        with open("tmp_code.py", "w") as file:
            file.write(parsed_code)  
        try:
            result = subprocess.run(["python", "tmp_code.py"], capture_output=True, text=True, check=True)
            return f"\nOutput:\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            return f"Errors:\n{e.stderr}\nOutput:\n{e.stdout}"
        finally:
            os.remove("tmp_code.py")
        
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

# Usage:

# tool = PythonRuntimeTool()

# code = """
# ```python
# import random
# import time

# time.sleep(5)
# random_list = [random.randint(1, 100) for _ in range(5)]
# print(random_list)
# ```
# """

# result = tool.execute_func(code)
# print(result)
