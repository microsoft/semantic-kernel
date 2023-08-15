import Levenshtein
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from retrying import retry

from semantic_kernel.skill_definition import (
    sk_function,
    sk_function_context_parameter,
)
from semantic_kernel.orchestration.sk_context import SKContext


class TokenBasedSimilarity:
    ## Get Embedding from OpenAI(Embeddings ADA)..
    @retry(
        stop_max_attempt_number=3,
        wait_incrementing_start=1000,
        wait_incrementing_increment=1000,
    )
    def get_embedding(text: str, context: SKContext):
        try:
            ## Set openai parameters..
            openai.api_type = "azure"
            # openai.api_version = "2023-03-15-preview"
            openai.api_version = "2023-07-01-preview"
            openai.api_key = context["api_key"]
            openai.api_base = context["endpoint"]
            embeddings_deployment = str(context["embeddings_deployment"])

            # print("embeddings_deployment", embeddings_deployment)

            response = openai.Embedding.create(
                input=text, deployment_id=embeddings_deployment
            )
        except Exception as e:
            # Handle the exception and print the error details
            print("An error occurred:", e)

        return np.array(response["data"][0]["embedding"])

    @sk_function(
        description="Calculate Levenshtein distance fo two input strings",
        name="calc_levenshtein_distance",
    )
    @sk_function_context_parameter(
        name="expected_str",
        description="The first string to calculate Levenshtein distance",
    )
    @sk_function_context_parameter(
        name="generated_str",
        description="The second string to calculate Levenshtein distance",
    )
    def calc_levenshtein_distance(self, context: SKContext) -> str:
        try:
            expected_str = context["expected_str"]
            generated_str = context["generated_str"]

            divider = (
                len(expected_str)
                if len(expected_str) > len(generated_str)
                else len(generated_str)
            )

            ## Calculate Levenshtein distance..
            lev_dist = Levenshtein.distance(expected_str, generated_str)
            lev_dist = lev_dist / divider
        except Exception as e:
            # Handle the exception and print the error details
            print("An error occurred:", e)

        return str(1 - lev_dist)

    @sk_function(
        description="Calculate Levenshtein diatance fo two input strings",
        name="calc_cosine_similarity",
    )
    @sk_function_context_parameter(
        name="expected_str",
        description="The first strting to calcualte cosine simialiry",
    )
    @sk_function_context_parameter(
        name="generated_str",
        description="The second string to calcualte cosine simialiry",
    )
    def calc_cosine_similarity(self, context: SKContext) -> str:
        cos_similarity = None

        try:
            expected_str = context["expected_str"]
            generated_str = context["generated_str"]

            expected_embedding = TokenBasedSimilarity.get_embedding(
                text=expected_str, context=context
            )
            generated_embedding = TokenBasedSimilarity.get_embedding(
                text=generated_str, context=context
            )

            cos_similarity = cosine_similarity(
                generated_embedding.reshape(1, -1), expected_embedding.reshape(1, -1)
            )[0][0]
        except Exception as e:
            # Handle the exception and print the error details
            print("An error occurred:", e)

        return str(cos_similarity)
