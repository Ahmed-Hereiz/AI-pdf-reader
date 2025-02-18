import requests
from typing import Any
from customAgents.agent_tools import BaseTool

class LinkedINApiTool(BaseTool):
    def __init__(self, linkedin_api_key: str, description: str, tool_name: str = None):
        super().__init__(description, tool_name)
        self.linkedin_api_key = linkedin_api_key
        self.base_url = "https://api.linkedin.com/v2"

    def execute_func(self, username: str) -> Any:
        """Retrieve account data for the provided username."""
        url = f"{self.base_url}/me"
        headers = {
            "Authorization": f"Bearer {self.linkedin_api_key}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Failed to retrieve data: {response.status_code}",
                "details": response.json()
            }

# Example usage:
# linkedin_tool = LinkedINApiTool(linkedin_api_key="your_api_key_here", description="LinkedIn API Tool")
# user_data = linkedin_tool.execute_func(username="your_username_here")
# print(user_data)
