from customAgents.runtime import BaseRuntime
from customAgents.agent_llm import BaseLLM
from customAgents.agent_prompt import BasePrompt


class HumanLoopRuntime(BaseRuntime):
    def __init__(self, llm: BaseLLM, prompt: BasePrompt):
        super().__init__(llm=llm, prompt=prompt, toolkit=[])


    def step(self) -> str:
        return super().step()
    
    def loop(self, activate_loop=True) -> str:
        
        if activate_loop:
            while activate_loop:
                agent_response = self.step()
                self.prompt.prompt += agent_response

                if activate_loop:
                    human_feedback = input("\n\nEnter feedback (or 'exit' to end loop): ")

                    if human_feedback.lower() == 'exit':
                        activate_loop = False
                    else:
                        self.prompt.prompt += f"\n\n### Feedback\n{human_feedback}\n"
        else:
            agent_response = self.step()

        return agent_response

