from typing import List, Any, Optional
from customAgents.runtime import BaseRuntime
from customAgents.tool_routers import BaseRouter


class BaseEnv:
    def __init__(self, agents: List[BaseRuntime], routers: List[BaseRouter] = None):
        self.agents = agents
        self.routers = routers if routers else []

    def run(self):
        """modify this in every class you create that inherit from BaseEnv"""
        for agent in self.agents:
            print(f"agent in the agents list : {agent}")

        raise NotImplementedError(f"Need to implement the run method first to specify how the env will work")

    def add_agent(self, agent: BaseRuntime) -> None:
        """Add a single agent to the environment"""
        self.agents.append(agent)

    def add_router(self, router: BaseRouter) -> None:
        """Add a single router to the environment"""
        self.routers.append(router)

    def remove_agent(self, agent: BaseRuntime) -> None:
        """Remove an agent from the environment"""
        if agent in self.agents:
            self.agents.remove(agent)

    def remove_router(self, router: BaseRouter) -> None:
        """Remove a router from the environment"""
        if router in self.routers:
            self.routers.remove(router)

    def get_agent_by_id(self, agent_id: str) -> Optional[BaseRuntime]:
        """Get an agent by its ID"""
        for agent in self.agents:
            if hasattr(agent, 'id') and agent.id == agent_id:
                return agent
        return None

    def clear(self) -> None:
        """Clear all agents and routers from the environment"""
        self.agents = []
        self.routers = []

    def __str__(self) -> str:
        return f"agents in this env is {self.agents}, routers in this env is {self.routers}"
    
    def __add__(self, other) -> 'BaseEnv':
        """Combine two environments"""
        self.agents.extend(other.agents)
        self.routers.extend(other.routers)
        return self

    def __len__(self) -> int:
        """Return the total number of agents and routers"""
        return len(self.agents) + len(self.routers)

    def __repr__(self) -> str:
        return f"BaseEnv(agents={self.agents}, routers={self.routers})"
