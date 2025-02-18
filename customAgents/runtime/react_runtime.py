import warnings
from typing import Dict
from colorama import Fore, Style
from customAgents.runtime import BaseRuntime
from customAgents.agent_llm import BaseLLM
from customAgents.agent_prompt import BasePrompt
from customAgents.agent_tools import ToolKit


class ReActRuntime(BaseRuntime):
    def __init__(self, llm: BaseLLM, prompt: BasePrompt, toolkit: ToolKit):

        super().__init__(llm, prompt, toolkit)


    def step(self) -> str:
        response = super().step()
        return self._parse_response(response=response)
    
    def loop(self, agent_max_steps: int = 5, verbose_tools: bool = False) -> str:

        if len(self.toolkit) != 0:
            self.prompt.prompt = self.prompt.prompt.replace("{tool_names}",' '.join(self.toolkit.tool_names))
            self.prompt.prompt = self.prompt.prompt.replace("{tools_and_role}",self.toolkit.tool_instructions)
            unempty_toolkit = 1
        else:
            self.prompt.prompt = self.prompt.prompt.replace("{tool_names}",'**No tools provided in this case I will just use my own thoughts**')
            self.prompt.prompt = self.prompt.prompt.replace("{tools_and_role}","(no tools so no actions... don't generate any action other than finish once you are sure about the answer)")
            unempty_toolkit = 0

        for _ in range(agent_max_steps):

            print("\n")
            agent_response = self.step()

            if agent_response['Action'].lower() == 'finish':
                final_answer = agent_response['Final Answer']
                print("\n")
                return final_answer
            
            if unempty_toolkit:
                if agent_response['Action'] not in self.toolkit.tool_names:
                    raise Exception(f"Unknown action: {agent_response['Action']}")

                try:
                    tool_result = self.toolkit.execute_tool(agent_response['Action'], agent_response['Action Input'])
                except Exception as e:
                    tool_result = None
                    error_message = str(e) 
                    warnings.warn(f"Tool execution failed with error: {error_message}")

                if tool_result == None:
                    warnings.warn("Tool is giving no results (Rerunning the loop again) please check the tools")
                elif len(tool_result) == 0:
                    warnings.warn("Tool is giving no empty list (Rerunning the loop again) please check the tools")

                if verbose_tools:
                    print(Fore.LIGHTYELLOW_EX + f"Tool Results :\n{tool_result}" + Style.RESET_ALL)
            
                self.prompt.prompt += f"Thought: {agent_response['Thought']}\nAction: {agent_response['Action']}\nAction Input: {agent_response['Action Input']}\nObservation: {tool_result}"

            else:
                self.prompt.prompt += f"Thought: {agent_response['Thought']}\nAction: {agent_response['Action']}\nAction Input: {agent_response['Action Input']}\nObservation: No tool used (I have to deal with the previous given text with my own thoughts without any external tool in this case)"

        return "Max iterations reached without finding an answer."
    

    def _parse_response(self, response: str) -> Dict[str, str]:
        parsed = {}
        current_key = None
        multiline_value = False

        for line in response.split('\n'):
            if ':' in line and not multiline_value:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if key in ['Thought', 'Action', 'Action Input', 'Observation', 'Final Answer']:
                    current_key = key
                    if key == 'Action Input':
                        multiline_value = True
                        parsed[current_key] = value
                    elif key == 'Final Answer':
                        parsed[current_key] = response.split('Final Answer:', 1)[1].strip()  
                        return parsed
                    else:
                        parsed[current_key] = value
            elif multiline_value and current_key == 'Action Input':
                parsed[current_key] += '\n' + line.strip()
                if line.strip().endswith('```'):
                    multiline_value = False
            elif current_key:
                parsed[current_key] += ' ' + line.strip()

        return parsed


