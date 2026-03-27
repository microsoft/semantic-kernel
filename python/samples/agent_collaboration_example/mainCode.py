import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.agents import Agent

kernel = Kernel()

kernel.add_service(
    OpenAIChatCompletion(
        service_id="chat",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-3.5-turbo"
    )
)

planner = Agent(
    name="Planner",
    instructions="Break the task into steps."
)

executor = Agent(
    name="Executor",
    instructions="Execute the plan and produce a final answer."
)

task = "Explain how AI agents collaborate."

plan = planner.invoke(kernel, task)
result = executor.invoke(kernel, plan)

print(result)
