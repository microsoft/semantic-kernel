# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncGenerator
from typing import Any, Literal, override

import graphrag.api as api
import pandas as pd
import yaml
from graphrag.config.create_graphrag_config import GraphRagConfig, create_graphrag_config
from graphrag.index.typing import PipelineRunResult

from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent, StreamingChatMessageContent

from .graphrag_prompt_execution_settings import GraphRagPromptExecutionSettings

logger = logging.getLogger(__name__)


class GraphRagChatCompletion(ChatCompletionClientBase):
    """GraphRagChatCompletion is a class that extends ChatCompletionClientBase to provide
    chat completion functionalities using a GraphRag setup.

    Attributes:
        project_directory (str): The directory where the project files are located.
        graphrag_config (GraphRagConfig): Configuration for the GraphRag service.
        final_nodes (pd.DataFrame | None): DataFrame containing the final nodes.
        final_entities (pd.DataFrame | None): DataFrame containing the final entities.
        final_communities (pd.DataFrame | None): DataFrame containing the final communities.
        final_community_reports (pd.DataFrame | None): DataFrame containing the final community reports.
        final_documents (pd.DataFrame | None): DataFrame containing the final documents.
        final_relationships (pd.DataFrame | None): DataFrame containing the final relationships.
        final_text_units (pd.DataFrame | None): DataFrame containing the final text units.
    """

    project_directory: str
    graphrag_config: GraphRagConfig
    final_nodes: pd.DataFrame | None = None
    final_entities: pd.DataFrame | None = None
    final_communities: pd.DataFrame | None = None
    final_community_reports: pd.DataFrame | None = None
    final_documents: pd.DataFrame | None = None
    final_relationships: pd.DataFrame | None = None
    final_text_units: pd.DataFrame | None = None

    def __init__(
        self, project_directory: str, service_id: str = "graph_rag", graphrag_config: GraphRagConfig | None = None
    ):
        """
        Initializes the GraphRagChatCompletion instance.

        Args:
            project_directory (str): The directory where the project files are located.
            service_id (str): The service identifier. Defaults to "graph_rag".
            graphrag_config (GraphRagConfig | None): Configuration for the GraphRag service.
                If None, it will be loaded from settings.yaml.
        """
        if not graphrag_config:
            with open(f"{project_directory}/settings.yaml") as file:
                graphrag_config = create_graphrag_config(values=yaml.safe_load(file), root_dir=project_directory)
        super().__init__(
            service_id=service_id,
            ai_model_id=service_id,
            project_directory=project_directory,
            graphrag_config=graphrag_config,
        )

    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        """
        Returns the class type for prompt execution settings.

        Returns:
            type[PromptExecutionSettings]: The class type for prompt execution settings.
        """
        return GraphRagPromptExecutionSettings

    async def setup(self):
        """Sets up the GraphRagChatCompletion instance by building the index and loading the necessary data."""

        index_result: list[PipelineRunResult] = await api.build_index(config=self.graphrag_config)

        # index_result is a list of workflows that make up the indexing pipeline that was run
        for workflow_result in index_result:
            status = f"error\n{workflow_result.errors}" if workflow_result.errors else "success"
            print(f"Workflow Name: {workflow_result.workflow}\tStatus: {status}")
        self.load()

    def has_loaded(self, search_type: Literal["local", "global", "drift"] | None = None) -> bool:
        """Checks if the necessary data has been loaded based on the search type.

        Args:
            search_type (Literal["local", "global", "drift"] | None): The type of search to check for.

        Returns:
            bool: True if the necessary data has been loaded, False otherwise.
        """
        if search_type == "local":
            return all([
                self.final_nodes is not None,
                self.final_entities is not None,
                self.final_communities is not None,
                self.final_community_reports is not None,
                self.final_text_units is not None,
                self.final_relationships is not None,
            ])
        if search_type == "global":
            return all([
                self.final_nodes is not None,
                self.final_entities is not None,
                self.final_communities is not None,
                self.final_community_reports is not None,
            ])
        if search_type == "drift":
            return all([
                self.final_nodes is not None,
                self.final_entities is not None,
                self.final_communities is not None,
                self.final_community_reports is not None,
                self.final_text_units is not None,
                self.final_relationships is not None,
            ])
        return all([
            self.final_nodes is not None,
            self.final_entities is not None,
            self.final_communities is not None,
            self.final_community_reports is not None,
            self.final_text_units is not None,
            self.final_relationships is not None,
            self.final_documents is not None,
        ])

    def post_model_init(self, *args, **kwargs):
        """Post-initialization method to load the necessary data after the model has been initialized."""
        try:
            self.load()
        except FileNotFoundError:
            logger.warning(
                "Could not load the final nodes, entities, communities, and community reports. Please run setup first."
            )

    def load(self):
        """Loads the parquet files.

        Includes final nodes, entities, communities, community reports, text units, relationships, and documents."""

        self.final_nodes = pd.read_parquet(f"{self.project_directory}/output/create_final_nodes.parquet")
        self.final_entities = pd.read_parquet(f"{self.project_directory}/output/create_final_entities.parquet")
        self.final_communities = pd.read_parquet(f"{self.project_directory}/output/create_final_communities.parquet")
        self.final_community_reports = pd.read_parquet(
            f"{self.project_directory}/output/create_final_community_reports.parquet"
        )
        self.final_text_units = pd.read_parquet(f"{self.project_directory}/output/create_final_text_units.parquet")
        self.final_relationships = pd.read_parquet(
            f"{self.project_directory}/output/create_final_relationships.parquet"
        )
        self.final_documents = pd.read_parquet(f"{self.project_directory}/output/create_final_documents.parquet")

    @override
    async def _inner_get_chat_completion_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        # Make sure the settings is of type GraphRagPromptExecutionSettings
        if not isinstance(settings, GraphRagPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        # Check if the necessary data has been loaded
        if not self.has_loaded(search_type=settings.search_type):
            raise ValueError("The required assets have not been loaded, please run setup first.")
        if settings.search_type == "global":
            # Call the global search
            response, context = await api.global_search(
                config=self.graphrag_config,
                nodes=self.final_nodes,
                entities=self.final_entities,
                communities=self.final_communities,
                community_reports=self.final_community_reports,
                community_level=2,
                dynamic_community_selection=False,
                response_type=settings.response_type,
                query=chat_history.messages[-1].content,
            )
            # since the response is a string, we can wrap it into a ChatMessageContent
            # we store the context in the metadata of the message.
            if isinstance(response, str):
                cmc = ChatMessageContent(role=AuthorRole.ASSISTANT, content=response, metadata={"context": context})
                return [cmc]
            raise ValueError("Unknown response type.")
        if settings.search_type == "local":
            # Call the local search
            response, context = await api.local_search(
                config=self.graphrag_config,
                nodes=self.final_nodes,
                entities=self.final_entities,
                community_reports=self.final_community_reports,
                text_units=self.final_text_units,
                relationships=self.final_relationships,
                covariates=None,
                community_level=2,
                response_type=settings.response_type,
                query=chat_history.messages[-1].content,
            )
            # since the response is a string, we can wrap it into a ChatMessageContent
            # we store the context in the metadata of the message.
            if isinstance(response, str):
                cmc = ChatMessageContent(role=AuthorRole.ASSISTANT, content=response, metadata={"context": context})
                return [cmc]
            raise ValueError("Unknown response type.")
        # Call the drift search
        response, context = await api.drift_search(
            config=self.graphrag_config,
            nodes=self.final_nodes,
            entities=self.final_entities,
            community_reports=self.final_community_reports,
            text_units=self.final_text_units,
            relationships=self.final_relationships,
            community_level=2,
            query=chat_history.messages[-1].content,
        )
        # since the response is a string, we can wrap it into a ChatMessageContent
        # we store the context in the metadata of the message.
        if isinstance(response, str):
            cmc = ChatMessageContent(role=AuthorRole.ASSISTANT, content=response, metadata={"context": context})
            return [cmc]
        raise ValueError("Unknown response type.")

    @override
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        # Make sure the settings is of type GraphRagPromptExecutionSettings
        if not isinstance(settings, GraphRagPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        # Check if the necessary data has been loaded
        if not self.has_loaded(search_type=settings.search_type):
            raise ValueError("The required assets have not been loaded, please run setup first.")
        if settings.search_type == "drift":
            # Drift search is not available when streaming
            raise NotImplementedError("Drift search is not available when streaming.")
        if settings.search_type == "global":
            # Call the global search
            responses = api.global_search_streaming(
                config=self.graphrag_config,
                nodes=self.final_nodes,
                entities=self.final_entities,
                communities=self.final_communities,
                community_reports=self.final_community_reports,
                community_level=2,
                dynamic_community_selection=False,
                response_type=settings.response_type,
                query=chat_history.messages[-1].content,
            )
        else:
            # Call the local search
            responses = api.local_search_streaming(
                config=self.graphrag_config,
                nodes=self.final_nodes,
                entities=self.final_entities,
                community_reports=self.final_community_reports,
                text_units=self.final_text_units,
                relationships=self.final_relationships,
                covariates=None,
                community_level=2,
                response_type=settings.response_type,
                query=chat_history.messages[-1].content,
            )
        async for response in responses:
            # the reponse is either a string (the response) or a dict (the context)
            if isinstance(response, str):
                # the response is a string, we can wrap it into a StreamingChatMessageContent
                cmc = StreamingChatMessageContent(choice_index=0, role=AuthorRole.ASSISTANT, content=response)
                yield [cmc]
            if isinstance(response, dict):
                # the response is a dict, we can add it to a metadata field of a StreamingChatMessageContent
                cmc = StreamingChatMessageContent(
                    choice_index=0, content="", role=AuthorRole.ASSISTANT, metadata={"context": response}
                )
                yield [cmc]
