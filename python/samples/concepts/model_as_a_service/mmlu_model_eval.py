# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from datasets import Dataset, DatasetDict, load_dataset
from huggingface_hub import login
from tqdm import tqdm

from samples.concepts.model_as_a_service.helpers import (
    expected_answer_to_letter,
    formatted_question,
    formatted_system_message,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_chat_completion import (
    AzureAIInferenceChatCompletion,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel


def setup_kernel():
    """Set up the kernel with AI services."""
    kernel = Kernel()
    kernel.add_service(
        AzureAIInferenceChatCompletion(
            ai_model_id="Llama3-8b",
            api_key="",
            endpoint="",
        )
    )
    kernel.add_service(
        AzureAIInferenceChatCompletion(
            ai_model_id="Phi3-mini",
            api_key="",
            endpoint="",
        )
    )
    kernel.add_service(
        AzureAIInferenceChatCompletion(
            ai_model_id="Phi3-small",
            api_key="",
            endpoint="",
        )
    )

    # Add the plugin
    kernel.add_plugin(MMLUPlugin(), "MMLUPlugin")

    return kernel


def load_mmlu_dataset(subjects: list[str]) -> dict[str, Dataset]:
    """Load a dataset."""
    login()

    datasets = {}
    number_of_samples = 0
    for subject in subjects:
        ds: DatasetDict = load_dataset("cais/mmlu", name=subject)
        validation_ds: Dataset = ds["validation"]
        datasets[subject] = validation_ds
        print(f"Loaded MMLU validation dataset for {subject}. This dataset has {validation_ds.num_rows} examples.")

        number_of_samples += validation_ds.num_rows

    print(f"Loaded {len(subjects)} datasets with a total of {number_of_samples} examples.")

    return datasets


class MMLUPlugin:
    """A plugin for evaluating the MMLU dataset."""

    @kernel_function(name="evaluate", description="Run a sample and return if the answer was correct.")
    async def evaluate(
        self,
        sample: Annotated[dict, "The sample"],
        subject: Annotated[str, "The subject of the sample"],
        kernel: Annotated[Kernel, "The kernel"],
        service_id: Annotated[str, "The service id"],
    ) -> Annotated[bool, "Whether the answer was correct"]:
        """Run a sample and return if the answer was correct.

        Args:
            sample (str): The sample containing the question and the correct answer.
            subject (str): The subject of the sample.
            kernel (Kernel): The kernel.
            service_id (str): The service id.

        Returns:
            bool: Whether the answer was correct.
        """
        chat_history = ChatHistory(system_message=formatted_system_message(subject))
        chat_history.add_user_message(
            formatted_question(
                sample["question"],
                sample["choices"][0],
                sample["choices"][1],
                sample["choices"][2],
                sample["choices"][3],
            ),
        )

        correct_answer = expected_answer_to_letter(sample["answer"])
        response = await kernel.get_service(service_id).get_chat_message_content(
            chat_history,
            settings=kernel.get_prompt_execution_settings_from_service_id(service_id),
        )

        if not response:
            return False

        return response.content.strip() == correct_answer


async def main():
    datasets = load_mmlu_dataset(
        [
            "college_computer_science",
            "astronomy",
            "college_biology",
            "college_chemistry",
            "elementary_mathematics",
            # Add more subjects here.
            # See here for a full list of subjects: https://huggingface.co/datasets/cais/mmlu/viewer
        ]
    )
    kernel = setup_kernel()
    ai_services = kernel.get_services_by_type(ChatCompletionClientBase).keys()

    # Total number of samples
    totals = sum([datasets[subject].num_rows for subject in datasets])
    # Total number of correct answers by each AI service
    total_corrects = {ai_service: 0.0 for ai_service in ai_services}
    for subject in datasets:
        # Number of correct answers by each AI service for this subject
        corrects = {ai_service: 0.0 for ai_service in ai_services}
        print(f"Evaluating {subject}...")
        for sample in tqdm(datasets[subject]):
            for ai_service in ai_services:
                kernel_arguments = KernelArguments(
                    sample=sample,
                    subject=subject,
                    kernel=kernel,
                    service_id=ai_service,
                )
                result = await kernel.invoke(
                    plugin_name="MMLUPlugin", function_name="evaluate", arguments=kernel_arguments
                )

                if result.value is True:
                    corrects[ai_service] += 1

        print(f"Finished evaluating {subject}.")
        for ai_service in ai_services:
            total_corrects[ai_service] += corrects[ai_service]
            print(f"Accuracy of {ai_service}: {corrects[ai_service] / datasets[subject].num_rows * 100:.2f}%.")

    print("Overall results:")
    for ai_service in ai_services:
        print(f"Overall Accuracy of {ai_service}: {total_corrects[ai_service] / totals * 100:.2f}%.")


if __name__ == "__main__":
    asyncio.run(main())
