# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from azure.ai.inference.aio import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from datasets import Dataset, DatasetDict, load_dataset
from huggingface_hub import login

from samples.concepts.model_as_a_service.helpers import formatted_question, formatted_system_message
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_chat_completion import (
    AzureAIInferenceChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

subject = "college_computer_science"

login()

ds: DatasetDict = load_dataset("cais/mmlu", name=subject)
validation_ds: Dataset = ds["validation"]

print(f"Loaded MMLU validation dataset for {subject}")
print(f"Number of examples: {validation_ds.num_rows}")
print(f"This dataset has the following columns: {validation_ds.column_names}")

azure_openai_settings = AzureOpenAISettings.create()
endpoint = azure_openai_settings.endpoint
deployment_name = azure_openai_settings.chat_deployment_name
api_key = azure_openai_settings.api_key.get_secret_value()

kernel = Kernel()
kernel.add_service(
    AzureAIInferenceChatCompletion(
        ai_model_id=deployment_name,
        client=ChatCompletionsClient(
            endpoint=f'{str(endpoint).strip("/")}/openai/deployments/{deployment_name}',
            credential=AzureKeyCredential(""),
            headers={"api-key": api_key},
        ),
    )
)
settings = kernel.get_prompt_execution_settings_from_service_id(deployment_name)
settings.max_tokens = 2000
settings.temperature = 0.1


class MMLUPlugin:
    """A plugin for generating static text."""

    @kernel_function(name="collect", description="Run a question and return the answer")
    async def collect(self, question: Annotated[str, "The question"]) -> Annotated[str, "The answer to the question"]:
        """Run a question and return the answer.

        Args:
            question (str): The question to answer.

        Returns:
            str: The answer to the question.
        """
        chat_history = ChatHistory(system_message=formatted_system_message(subject))
        chat_history.add_user_message(question)

        responses = await kernel.get_service(deployment_name).get_chat_message_contents(chat_history, settings)
        if len(responses) == 0:
            return "I'm sorry, I don't have an answer for that question."
        return responses[0].content


mmlu_plugin = kernel.add_plugin(MMLUPlugin(), "MMLUPlugin")


async def main():
    for sample in validation_ds:
        kernel_arguments = KernelArguments(
            question=formatted_question(
                sample["question"],
                sample["choices"][0],
                sample["choices"][1],
                sample["choices"][2],
                sample["choices"][3],
            )
        )
        answer = await kernel.invoke(mmlu_plugin["collect"], kernel_arguments)
        print(answer)


if __name__ == "__main__":
    asyncio.run(main())
