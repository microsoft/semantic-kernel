# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncGenerator
from typing import Any, Literal

import graphrag.api as api
import pandas as pd
import yaml
from graphrag.config.create_graphrag_config import GraphRagConfig, create_graphrag_config
from graphrag.index.typing import PipelineRunResult

from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent, StreamingChatMessageContent


class GraphRagPromptExecutionSettings(PromptExecutionSettings):
    response_type: str = "Multiple Paragraphs"
    search_type: Literal["local", "global", "drift"] = "global"


logger = logging.getLogger(__name__)


class GraphRagChatCompletion(ChatCompletionClientBase):
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
        return GraphRagPromptExecutionSettings

    async def setup(self):
        index_result: list[PipelineRunResult] = await api.build_index(config=self.graphrag_config)

        # index_result is a list of workflows that make up the indexing pipeline that was run
        for workflow_result in index_result:
            status = f"error\n{workflow_result.errors}" if workflow_result.errors else "success"
            print(f"Workflow Name: {workflow_result.workflow}\tStatus: {status}")
        self.load()

    def has_loaded(self, search_type: Literal["local", "global", "drift"] | None = None) -> bool:
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
        try:
            self.load()
        except FileNotFoundError:
            logger.warning(
                "Could not load the final nodes, entities, communities, and community reports. Please run setup first."
            )

    def load(self):
        """Load the final nodes, entities, communities, and community reports."""
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

    async def _inner_get_chat_completion_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, GraphRagPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        if not self.has_loaded(search_type=settings.search_type):
            raise ValueError("The required assets have not been loaded, please run setup first.")
        if settings.search_type == "global":
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
            if isinstance(response, str):
                cmc = ChatMessageContent(role=AuthorRole.ASSISTANT, content=response, metadata={"context": context})
                return [cmc]
            raise ValueError("Unknown response type.")
        if settings.search_type == "local":
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
            if isinstance(response, str):
                cmc = ChatMessageContent(role=AuthorRole.ASSISTANT, content=response, metadata={"context": context})
                return [cmc]
            raise ValueError("Unknown response type.")
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
        if isinstance(response, str):
            cmc = ChatMessageContent(role=AuthorRole.ASSISTANT, content=response, metadata={"context": context})
            return [cmc]
        raise ValueError("Unknown response type.")

    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, GraphRagPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        if not self.has_loaded(search_type=settings.search_type):
            raise ValueError("The required assets have not been loaded, please run setup first.")
        if settings.search_type == "global":
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
            async for response in responses:
                if isinstance(response, str):
                    cmc = StreamingChatMessageContent(choice_index=0, role=AuthorRole.ASSISTANT, content=response)
                    yield [cmc]
                if isinstance(response, dict):
                    cmc = StreamingChatMessageContent(
                        choice_index=0, content="", role=AuthorRole.ASSISTANT, metadata={"context": response}
                    )
                    yield [cmc]
            return
        elif settings.search_type == "local":
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
                if isinstance(response, str):
                    cmc = StreamingChatMessageContent(choice_index=0, role=AuthorRole.ASSISTANT, content=response)
                    yield [cmc]
                if isinstance(response, dict):
                    cmc = StreamingChatMessageContent(
                        choice_index=0, content="", role=AuthorRole.ASSISTANT, metadata={"context": response}
                    )
                    yield [cmc]
            return
        raise NotImplementedError("Drift search is not available when streaming.")


async def chat(service: ChatCompletionClientBase, chat_history: ChatHistory) -> bool:
    try:
        user_input = input("User:> ")
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    # Add the user message to the chat history so that the chatbot can respond to it.
    chat_history.add_user_message(user_input)

    # Get the chat message content from the chat completion service.
    # The response is an async generator that streams the response in chunks.
    response = service.get_streaming_chat_message_content(
        chat_history=chat_history,
        settings=GraphRagPromptExecutionSettings(search_type="local"),
    )

    # Capture the chunks of the response and print them as they come in.
    chunks: list[StreamingChatMessageContent] = []
    print("Mosscap:> ", end="")
    async for chunk in response:
        if chunk:
            chunks.append(chunk)
            print(chunk, end="")
    print("")

    # Combine the chunks into a single message to add to the chat history.
    full_message = sum(chunks[1:], chunks[0])
    print("Context:")
    for part in ["reports", "entities", "relationships", "claims", "sources"]:
        print(f"  {part}:")
        for values in full_message.metadata["context"][part]:
            if isinstance(values, dict):
                for key, value in values.items():
                    print(f"    {key}:{value}")
            else:
                print(f"    {values}")
    print("done")
    # Add the chat message to the chat history to keep track of the conversation.
    chat_history.add_message(full_message)

    return True


async def main():
    graph_rag_chat_completion = GraphRagChatCompletion(project_directory="./ragtest")
    if not graph_rag_chat_completion.has_loaded():
        await graph_rag_chat_completion.setup()
    chat_history = ChatHistory()
    while await chat(graph_rag_chat_completion, chat_history):
        pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
