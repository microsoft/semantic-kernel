# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any, Type, TypeVar

from semantic_kernel.agents.agent import Agent
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException

if TYPE_CHECKING:
    pass

_TAgent = TypeVar("_TAgent", bound=Agent)

# Global agent type registry
AGENT_TYPE_REGISTRY: dict[str, Type[Agent]] = {}


def register_agent_type(agent_type: str):
    """Decorator to register an agent type with the registry."""

    def decorator(cls: Type[_TAgent]) -> Type[_TAgent]:
        AGENT_TYPE_REGISTRY[agent_type.lower()] = cls
        return cls

    return decorator


class AgentRegistry:
    """Responsible for creating agents from YAML, dicts, or files."""

    @staticmethod
    def register_type(agent_type: str, agent_cls: Type[Agent]) -> None:
        """Register a new agent type at runtime.

        Args:
            agent_type: The string identifier representing the agent type (e.g., 'chat_completion_agent').
            agent_cls: The class implementing the agent, inheriting from `Agent`.

        Example:
            AgentRegistry.register_type("my_custom_agent", MyCustomAgent)
        """
        AGENT_TYPE_REGISTRY[agent_type.lower()] = agent_cls

    @staticmethod
    async def create_agent_from_yaml(
        yaml_str: str,
        *,
        kernel,
        settings: Any = None,
        **kwargs,
    ) -> _TAgent:
        """Create a single agent instance from a YAML string.

        Args:
            yaml_str: The YAML string defining the agent.
            kernel: The Kernel instance to use for tool resolution and agent initialization.
            service: An AI service instance (for example, AzureChatCompletion) to inject into the agent.
            **kwargs: Additional parameters passed to the agent constructor if required.

        Returns:
            An instance of the requested agent.

        Raises:
            AgentInitializationException: If the YAML is invalid or the agent type is not supported.

        Example:
            agent = await AgentRegistry.create_agent_from_yaml(
                yaml_str, kernel=kernel, service=AzureChatCompletion(),
            )
        """
        import yaml

        data = yaml.safe_load(yaml_str)

        agent_type = data.get("type", "").lower()

        if not agent_type:
            raise AgentInitializationException("Missing 'type' field in agent definition.")

        if agent_type not in AGENT_TYPE_REGISTRY:
            raise AgentInitializationException(f"Agent type '{agent_type}' not registered.")

        agent_cls = AGENT_TYPE_REGISTRY[agent_type]

        # Let the agent class resolve placeholders, if needed
        if settings:
            yaml_str = agent_cls.resolve_placeholders(yaml_str, settings)

        return await AgentRegistry.create_agent_from_dict(
            data,
            kernel=kernel,
            settings=settings,
            **kwargs,
        )

    @staticmethod
    async def create_agent_from_dict(
        data: dict,
        *,
        kernel,
        settings: Any = None,
        **kwargs,
    ) -> _TAgent:
        """Create a single agent instance from a dictionary.

        Args:
            data: The dictionary defining the agent fields.
            kernel: The Kernel instance to use for tool resolution and agent initialization.
            service: An AI service instance (for example, AzureChatCompletion) to inject into the agent.
            **kwargs: Additional parameters passed to the agent constructor if required.

        Returns:
            An instance of the requested agent.

        Raises:
            AgentInitializationException: If the dictionary is missing a 'type' field or the agent type is unsupported.

        Example:
            agent = await AgentRegistry.create_agent_from_dict(agent_data, kernel=kernel)
        """
        agent_type = data.get("type", "").lower()

        if not agent_type:
            raise AgentInitializationException("Missing 'type' field in agent definition.")

        if agent_type not in AGENT_TYPE_REGISTRY:
            raise AgentInitializationException(f"Agent type '{agent_type}' is not supported.")

        agent_cls = AGENT_TYPE_REGISTRY[agent_type]

        # Inject service if needed
        return await agent_cls.from_dict(
            data,
            kernel=kernel,
            settings=settings,
            **kwargs,
        )

    @staticmethod
    async def create_agents_from_yaml(
        yaml_str: str,
        *,
        kernel,
        **kwargs,
    ) -> list[_TAgent]:
        """Create multiple agent instances from a YAML list.

        Args:
            yaml_str: A YAML string defining a list of agent specifications.
            kernel: The Kernel instance to use for tool resolution and agent initialization.
            service: An AI service instance (for example, AzureChatCompletion to inject into each created agent.
            **kwargs: Additional parameters passed to each agent constructor if required.

        Returns:
            A list of created agent instances.

        Raises:
            AgentInitializationException: If the YAML does not contain a valid list of agents.

        Example:
            agents = await AgentRegistry.create_agents_from_yaml(multi_agent_yaml, kernel=kernel)
        """
        import yaml

        raw = yaml.safe_load(yaml_str)

        if not isinstance(raw, list):
            raise AgentInitializationException("Expected a list of agents in YAML for batch creation.")

        agents: list[Agent] = []
        for agent_data in raw:
            agent = await AgentRegistry.create_agent_from_dict(
                agent_data,
                kernel=kernel,
                **kwargs,
            )
            agents.append(agent)

        return agents
