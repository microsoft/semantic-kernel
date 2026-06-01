# Copyright (c) Microsoft. All rights reserved.

"""
OSOP Workflow Reader for Semantic Kernel

Reads an OSOP (.osop.yaml) workflow definition and creates
Semantic Kernel ChatCompletionAgents from the agent nodes.
Demonstrates how portable OSOP workflow definitions can drive
SK agent orchestration.

Usage:
    python osop_workflow_reader.py
"""

import asyncio
from pathlib import Path

import yaml

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

# OSOP node type → SK description
NODE_TYPE_DESCRIPTIONS = {
    "agent": "AI agent (ChatCompletionAgent)",
    "api": "API call (native function)",
    "cli": "CLI command execution",
    "human": "Human review step",
    "system": "System/infrastructure",
    "db": "Database operation",
}


def load_osop_workflow(file_path: str) -> dict:
    """Load and parse an OSOP workflow YAML file."""
    content = Path(file_path).read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    if not isinstance(data, dict) or "nodes" not in data:
        raise ValueError("Invalid OSOP workflow: missing 'nodes'")
    return data


def describe_workflow(workflow: dict) -> str:
    """Generate a human-readable description of an OSOP workflow."""
    name = workflow.get("name", workflow.get("id", "Untitled"))
    nodes = workflow.get("nodes", [])
    edges = workflow.get("edges", [])
    lines = [f"Workflow: {name}", f"Nodes: {len(nodes)}, Edges: {len(edges)}", ""]
    for node in nodes:
        ntype = node.get("type", "system")
        nname = node.get("name", node.get("id", "?"))
        desc = NODE_TYPE_DESCRIPTIONS.get(ntype, ntype)
        lines.append(f"  [{ntype}] {nname} — {desc}")
    return "\n".join(lines)


async def create_agents_from_osop(workflow: dict, kernel: Kernel) -> list[ChatCompletionAgent]:
    """Create SK ChatCompletionAgents from OSOP agent nodes."""
    agents = []
    for node in workflow.get("nodes", []):
        if node.get("type") != "agent":
            continue
        name = node.get("name", node.get("id", "Agent"))
        purpose = node.get("purpose", node.get("description", ""))
        config = node.get("config", {})
        system_prompt = config.get("system_prompt", f"You are {name}. {purpose}")

        agent = ChatCompletionAgent(
            kernel=kernel,
            name=name.replace(" ", "_"),
            instructions=system_prompt,
        )
        agents.append(agent)
        print(f"  Created agent: {name}")
    return agents


async def main():
    # Load the OSOP workflow
    osop_path = Path(__file__).parent / "code-review-pipeline.osop.yaml"
    if not osop_path.exists():
        print(f"OSOP file not found: {osop_path}")
        return

    workflow = load_osop_workflow(str(osop_path))
    print(describe_workflow(workflow))
    print()

    # Create a kernel with OpenAI
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id="default"))

    # Create agents from OSOP definition
    print("Creating agents from OSOP workflow:")
    agents = await create_agents_from_osop(workflow, kernel)
    print(f"\nCreated {len(agents)} agents from {len(workflow.get('nodes', []))} OSOP nodes")

    # Demonstrate: use the first agent
    if agents:
        thread = ChatHistoryAgentThread()
        print(f"\nInvoking agent: {agents[0].name}")
        response = await agents[0].get_response(
            messages="Describe a simple Python function that calculates factorial.",
            thread=thread,
        )
        print(f"Response: {response.content[:200]}...")


if __name__ == "__main__":
    asyncio.run(main())
