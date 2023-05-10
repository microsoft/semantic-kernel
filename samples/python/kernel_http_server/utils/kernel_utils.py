import os
import logging
import inspect
from typing import List
import azure.functions as func
import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai

from utils.config import AIService, headers_to_config


def sample_skills_path() -> str:
    PARENT = "samples"
    FOLDER = "skills"

    def search_path(path_to_find: str, max_attempts=10):
        curr_dir = os.path.abspath(inspect.getfile(inspect.currentframe()))
        found = False
        while max_attempts > 0 and not found:
            result = os.path.join(curr_dir, path_to_find)
            found = os.path.isdir(result)
            curr_dir = os.path.abspath(os.path.join(curr_dir, ".."))
            max_attempts -= 1

        return found, result

    found, path = search_path(PARENT + os.path.sep + FOLDER)
    if not found:
        found, path = search_path(FOLDER)

    if not found:
        raise ValueError(
            "Skills directory not found. The app needs the skills from the repo to work."
        )

    return path


def create_kernel_for_request(req: func.HttpRequest, skills: List[str], memory_store):
    """
    Creates a kernel for a request.
    :param req: The request.
    :param skills: The skills.
    :param memory_story: The memory story.
    :return: The kernel.
    """
    # Create a kernel.
    kernel = sk.Kernel()
    logging.info("Creating kernel and importing skills %s", skills)

    # Get the API configuration.
    api_config = headers_to_config(req.headers)

    if api_config.serviceid == AIService.OPENAI.value:
        # Add an OpenAI backend
        kernel.add_text_completion_service(
            "dv",
            sk_oai.OpenAITextCompletion(
                api_config.deployment_model_id, api_config.key, api_config.org_id
            ),
        )
    elif api_config.serviceid == AIService.AZURE_OPENAI.value:
        # Add an Azure backend
        kernel.add_text_completion_service(
            "dv",
            sk_oai.AzureTextCompletion(
                api_config.deployment_model_id, api_config.key, api_config.endpoint
            ),
        )

    register_semantic_skills(kernel, sample_skills_path(), skills)

    return kernel


def register_semantic_skills(kernel, skills_dir, skills: List[str]):
    """
    Registers the semantic skills or all skills if input skills list is None
    :param kernel: The kernel.
    :param skills: The skills.
    :return: None.
    """
    logging.info("Importing skills %s", skills)

    for skill_path in os.listdir(skills_dir):
        if os.path.isdir(os.path.join(skills_dir, skill_path)):
            should_load = skills is None or skill_path.lower() in skills
            if should_load:
                logging.info("loading skill %s", skill_path)
                kernel.import_semantic_skill_from_directory(skills_dir, skill_path)
