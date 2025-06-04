# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Annotated, Any, Literal, get_args, get_origin, get_type_hints

from pydantic import BaseModel, create_model
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function

from guided_conversation.utils.base_model_llm import BaseModelLLM
from guided_conversation.utils.conversation_helpers import Conversation, ConversationMessageType
from guided_conversation.utils.openai_tool_calling import ToolValidationResult
from guided_conversation.utils.plugin_helpers import PluginOutput, fix_error, update_attempts

ARTIFACT_ERROR_CORRECTION_SYSTEM_TEMPLATE = """<message role="system">You are a helpful, thoughtful, and meticulous assistant.
You are conducting a conversation with a user. Your goal is to complete an artifact as thoroughly as possible by the end of the conversation.
You have tried to update a field in the artifact, but the value you provided did not adhere \
to the constraints of the field as specified in the artifact schema.
You will be provided the history of your conversation with the user, the schema for the field, \
your previous attempt(s) at updating the field, and the error message(s) that resulted from your attempt(s).
Your task is to select the best possible action to take next:
1. Update artifact
- You should pick this action if you have a valid value to submit for the field in question.
2. Resume conversation
- You should pick this action if: (a) you do NOT have a valid value to submit for the field in question, and \
(b) you need to ask the user for more information in order to obtain a valid value. \
For example, if the user stated that their date of birth is June 2000, but the artifact field asks for the date of birth in the format \
"YYYY-MM-DD", you should resume the conversation and ask the user for the day.</message>

<message role="user">Conversation history:
{{ conversation_history }}

Schema:
{{ artifact_schema }}

Previous attempts to update the field "{{ field_name }}" in the artifact:
{{ previous_attempts }}</message>"""

UPDATE_ARTIFACT_TOOL = "update_artifact_field"
RESUME_CONV_TOOL = "resume_conversation"


class Artifact:
    """The Artifact plugin takes in a Pydantic base model, and robustly handles updating the fields of the model
    A typical use case is as a form an agent must complete throughout a conversation.
    Another use case is as a working memory for the agent.

    The primary interface is update_artifact, which takes in the field_name to update and its new value.
    Additionally, the chat_history is passed in to help the agent make informed decisions in case an error occurs.

    The Artifact also exposes several functions to access internal state:
    get_artifact_for_prompt, get_schema_for_prompt, and get_failed_fields.
    """

    def __init__(
        self, kernel: Kernel, service_id: str, input_artifact: BaseModel, max_artifact_field_retries: int = 2
    ) -> None:
        """
        Initialize the Artifact plugin with the given Pydantic base model.

        Args:
            kernel (Kernel): The Semantic Kernel instance to use for calling the LLM. Don't forget to set your
                req_settings since this class uses tool calling functionality from the Semantic Kernel.
            service_id (str): The service ID to use for the Semantic Kernel tool calling. One kernel can have multiple
                services. The service ID is used to identify which service to use for LLM calls. The Artifact object
                assumes that the service has tool calling capabilities and is some flavor of chat completion.
            input_artifact (BaseModel): The Pydantic base model to use as the artifact
            max_artifact_field_retries (int): The maximum number of times to retry updating a field in the artifact
        """
        logger = logging.getLogger(__name__)
        self.logger = logger

        self.id = "artifact_plugin"
        self.kernel = kernel
        self.service_id = service_id
        self.max_artifact_field_retries = max_artifact_field_retries

        self.original_schema = input_artifact.model_json_schema()
        self.artifact = self._initialize_artifact(input_artifact)

        # failed_artifact_fields maps a field name to a list of the history of the failed attempts to update it
        # dict: key = field, value = list of tuple[attempt, error message]
        self.failed_artifact_fields: dict[str, list[tuple[str, str]]] = {}

    # The following are the kernel functions that will be provided to the LLM call
    @kernel_function(
        name=UPDATE_ARTIFACT_TOOL,
        description="Sets the value of a field in the artifact",
    )
    def update_artifact_field(
        self,
        field: Annotated[str, "The name of the field to update in the artifact"],
        value: Annotated[str, "The value to set the field to"],
    ) -> None:
        pass

    @kernel_function(
        name=RESUME_CONV_TOOL,
        description="Resumes conversation to get more information from the user ",
    )
    def resume_conversation(self):
        pass

    async def update_artifact(self, field_name: str, field_value: Any, conversation: Conversation) -> PluginOutput:
        """The core interface for the Artifact plugin.
        This function will attempt to update the given field_name to the given field_value.
        If the field_value fails Pydantic validation, an LLM will determine one of two actions to take.
        Given the conversation as additional context the two actions are:
            - Retry the update the artifact by fixing the formatting using the previous failed attempts as guidance
            - Take no action or in other words, resume the conversation to ask the user for more information because the user gave incomplete or incorrect information

        Args:
            field_name (str): The name of the field to update in the artifact
            field_value (Any): The value to set the field to
            conversation (Conversation): The conversation object that contains the history of the conversation

        Returns:
            PluginOutput: An object with two fields: a boolean indicating success
            and a list of conversation messages that may have been generated.

            Several outcomes can happen:
            - The update may have failed due to
                - A field_name that is not valid in the artifact.
                - The field_value failing Pydantic validation and all retries failed.
                - The model failed to correctly call a tool.
                In this case, the boolean will be False and the list may contain a message indicating the failure.

            - The agent may have successfully updated the artifact or fixed it.
                In this case, the boolean will be True and the list will contain a message indicating the update and possibly intermediate messages.

            - The agent may have decided to resume the conversation.
                In this case, the boolean will be True and the messages may only contain messages indicated previous errors.
        """

        conversation_messages: list[ChatMessageContent] = []

        # Check if the field name is valid, and return with a failure message if not
        is_valid_field, msg = self._is_valid_field(field_name)
        if not is_valid_field:
            conversation_messages.append(msg)
            return PluginOutput(update_successful=False, messages=conversation_messages)

        # Try to update the field, and handle any errors that occur until the field is
        # successfully updated or skipped according to max_artifact_field_retries
        while True:
            try:
                # Check if there have been too many previous failed attempts to update the field
                if len(self.failed_artifact_fields.get(field_name, [])) >= self.max_artifact_field_retries:
                    self.logger.warning(f"Updating field {field_name} has failed too many times. Skipping.")
                    return False, conversation_messages

                # Attempt to update the artifact
                msg = self._execute_update_artifact(field_name, field_value)
                conversation_messages.append(msg)
                return PluginOutput(True, conversation_messages)
            except Exception as e:
                self.logger.warning(f"Error updating field {field_name}: {e}. Retrying...")
                # Handle update error will increment failed_artifact_fields, once it has failed
                # greater than self.max_artifact_field_retries the field will be skipped and the loop will break
                success, new_field_value = await self._handle_update_error(field_name, field_value, conversation, e)

                # The agent has successfully fixed the field.
                if success and new_field_value is not None:
                    self.logger.info(f"Agent successfully fixed field {field_name}. New value: {new_field_value}")
                    field_value = new_field_value
                # This is the case where the agent has decided to resume the conversation.
                elif success:
                    self.logger.info(
                        f"Agent could not fix the field itself & decided to resume conversation to fix field {field_name}"
                    )
                    return PluginOutput(True, conversation_messages)
                self.logger.warning(f"Agent failed to fix field {field_name}. Retrying...")
                # Otherwise, the agent has failed and we will go through the loop again

    def get_artifact_for_prompt(self) -> str:
        """Returns a formatted JSON-like representation of the current state of the fields artifact.
        Any fields that were failed are completely omitted.

        Returns:
            str: The string representation of the artifact.
        """
        failed_fields = self.get_failed_fields()
        return {k: v for k, v in self.artifact.model_dump().items() if k not in failed_fields}

    def get_schema_for_prompt(self, filter_one_field: str | None = None) -> str:
        """Gets a clean version of the original artifact schema, optimized for use in an LLM prompt.

        Args:
            filter_one_field (str | None): If this is provided, only the schema for this one field will be returned.

        Returns:
            str: The cleaned schema
        """

        def _clean_properties(schema: dict, failed_fields: list[str]) -> str:
            properties = schema.get("properties", {})
            clean_properties = {}
            for name, property_dict in properties.items():
                if name not in failed_fields:
                    cleaned_property = {}
                    for k, v in property_dict.items():
                        if k in ["title", "default"]:
                            continue
                        cleaned_property[k] = v
                    clean_properties[name] = cleaned_property

            clean_properties_str = str(clean_properties)
            clean_properties_str = clean_properties_str.replace("$ref", "type")
            clean_properties_str = clean_properties_str.replace("#/$defs/", "")
            return clean_properties_str

        # If filter_one_field is provided, only get the schema for that one field
        if filter_one_field:
            if not self._is_valid_field(filter_one_field):
                self.logger.error(f'Field "{filter_one_field}" is not a valid field in the artifact.')
                raise ValueError(f'Field "{filter_one_field}" is not a valid field in the artifact.')
            filtered_schema = {"properties": {filter_one_field: self.original_schema["properties"][filter_one_field]}}
            filtered_schema.update((k, v) for k, v in self.original_schema.items() if k != "properties")
            schema = filtered_schema
        else:
            schema = self.original_schema

        failed_fields = self.get_failed_fields()
        properties = _clean_properties(schema, failed_fields)
        if not properties:
            self.logger.error("No properties found in the schema.")
            raise ValueError("No properties found in the schema.")

        types_schema = schema.get("$defs", {})
        custom_types = []
        for type_name, type_info in types_schema.items():
            if f"'type': '{type_name}'" in properties:
                clean_schema = _clean_properties(type_info, [])
                if clean_schema != "{}":
                    custom_types.append(f"{type_name} = {clean_schema}")

        if custom_types:
            explanation = f"If you wanted to create a {type_name} object, for example, you would make a JSON object \
with the following keys: {', '.join(types_schema[type_name]['properties'].keys())}."
            custom_types_str = "\n".join(custom_types)
            return f"""{properties}

Here are the definitions for the custom types referenced in the artifact schema:
{custom_types_str}

{explanation}
Remember that when updating the artifact, the field will be the original field name in the artifact and the JSON object(s) will be the value."""
        else:
            return properties

    def get_failed_fields(self) -> list[str]:
        """Get a list of fields that have failed all attempts to update.

        Returns:
            list[str]: A list of field names that have failed all attempts to update.
        """
        fields = []
        for field, attempts in self.failed_artifact_fields.items():
            if len(attempts) >= self.max_artifact_field_retries:
                fields.append(field)
        return fields

    def _initialize_artifact(self, artifact_model: BaseModel) -> BaseModelLLM:
        """Create a new artifact model based on the one provided by the user
        with "Unanswered" set for all fields.

        Args:
            artifact_model (BaseModel): The Pydantic class provided by the user

        Returns:
            BaseModelLLM: The new artifact model with "Unanswered" set for all fields
        """
        modified_classes = self._modify_classes(artifact_model)
        artifact = self._modify_base_artifact(artifact_model, modified_classes)
        return artifact()

    def _get_type_if_subtype(self, target_type: type[Any], base_type: type[Any]) -> type[Any] | None:
        """Recursively checks the target_type to see if it is a subclass of base_type or a generic including base_type.

        Args:
            target_type: The type to check.
            base_type: The type to check against.

        Returns:
            The class type if target_type is base_type, a subclass of base_type, or a generic including base_type; otherwise, None.
        """
        origin = get_origin(target_type)
        if origin is None:
            if issubclass(target_type, base_type):
                return target_type
        else:
            # Recursively check if any of the arguments are the target type
            for arg in get_args(target_type):
                result = self._get_type_if_subtype(arg, base_type)
                if result is not None:
                    return result
        return None

    def _modify_classes(self, artifact_class: BaseModel) -> dict[str, type[BaseModelLLM]]:
        """Find all classes used as type hints in the artifact, and modify them to set 'Unanswered' as a default and valid value for all fields."""
        modified_classes = {}
        # Find any instances of BaseModel in the artifact class in the first "level" of type hints
        for field_name, field_type in get_type_hints(artifact_class).items():
            is_base_model = self._get_type_if_subtype(field_type, BaseModel)
            if is_base_model is not None:
                modified_classes[field_name] = self._modify_base_artifact(is_base_model)

        return modified_classes

    def _replace_type_annotations(
        self, field_annotation: type[Any] | None, modified_classes: dict[str, type[BaseModelLLM]]
    ) -> type:
        """Recursively replace type annotations with modified classes where applicable."""
        # Get the origin of the field annotation, which is the base type for generic types (e.g., List[str] -> list, Dict[str, int] -> dict)
        origin = get_origin(field_annotation)
        # Get the type arguments of the generic type (e.g., List[str] -> str, Dict[str, int] -> str, int)
        args = get_args(field_annotation)

        if origin is None:
            # The type is not generic; check if it's a subclass that needs to be replaced
            if isinstance(field_annotation, type) and issubclass(field_annotation, BaseModelLLM):
                return modified_classes.get(field_annotation.__name__, field_annotation)
            return field_annotation
        else:
            # The type is generic; recursively replace the type annotations of the arguments
            new_args = tuple(self._replace_type_annotations(arg, modified_classes) for arg in args)
            return origin[new_args]

    def _modify_base_artifact(
        self, artifact_model: type[BaseModelLLM], modified_classes: dict[str, type[BaseModelLLM]] | None = None
    ) -> type[BaseModelLLM]:
        """Create a new artifact model with 'Unanswered' as a default and valid value for all fields."""
        for _, field_info in artifact_model.model_fields.items():
            # Replace original classes with modified version
            if modified_classes is not None:
                field_info.annotation = self._replace_type_annotations(field_info.annotation, modified_classes)
            # This makes it possible to always set a field to "Unanswered"
            field_info.annotation = field_info.annotation | Literal["Unanswered"]
            # This sets the default value to "Unanswered"
            field_info.default = "Unanswered"
            # This adds "Unanswered" as a possible value to any regex patterns
            metadata = field_info.metadata
            for m in metadata:
                if hasattr(m, "pattern"):
                    m.pattern += "|Unanswered"
        field_definitions = {
            name: (field_info.annotation, field_info) for name, field_info in artifact_model.model_fields.items()
        }
        artifact_model = create_model("Artifact", __base__=BaseModelLLM, **field_definitions)
        return artifact_model

    def _is_valid_field(self, field_name: str) -> tuple[bool, ChatMessageContent]:
        """Check if the field_name is a valid field in the artifact. Returns True if it is, False and an error message otherwise."""
        if field_name not in self.artifact.model_fields:
            error_message = f'Field "{field_name}" is not a valid field in the artifact.'
            msg = ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content=error_message,
                metadata={"type": ConversationMessageType.ARTIFACT_UPDATE, "turn_number": None},
            )
            return False, msg
        return True, None

    async def _fix_artifact_error(
        self,
        field_name: str,
        previous_attempts: str,
        conversation_repr: str,
        artifact_schema_repr: str,
    ) -> dict[str, Any]:
        """Calls the LLM to fix an error in the artifact using Semantic Kernel kernel."""

        req_settings = self.kernel.get_prompt_execution_settings_from_service_id(self.service_id)
        req_settings.max_tokens = 2000

        self.kernel.add_function(plugin_name=self.id, function=self.update_artifact_field)
        self.kernel.add_function(plugin_name=self.id, function=self.resume_conversation)
        filter = {"included_plugins": [self.id]}
        req_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(auto_invoke=False, filters=filter)

        arguments = KernelArguments(
            field_name=field_name,
            conversation_history=conversation_repr,
            previous_attempts=previous_attempts,
            artifact_schema=artifact_schema_repr,
            settings=req_settings,
        )

        return await fix_error(
            kernel=self.kernel,
            prompt_template=ARTIFACT_ERROR_CORRECTION_SYSTEM_TEMPLATE,
            req_settings=req_settings,
            arguments=arguments,
        )

    def _execute_update_artifact(
        self,
        field_name: Annotated[str, "The name of the field to update in the artifact"],
        field_value: Annotated[Any, "The value to set the field to"],
    ) -> None:
        """Update a field in the artifact with a new value. This will raise an error if the field_value is invalid."""
        setattr(self.artifact, field_name, field_value)
        msg = ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            content=f"Assistant updated {field_name} to {field_value}",
            metadata={"type": ConversationMessageType.ARTIFACT_UPDATE, "turn_number": None},
        )
        return msg

    async def _handle_update_error(
        self, field_name: str, field_value: Any, conversation: Conversation, error: Exception
    ) -> tuple[bool, Any]:
        """
        Handles the logic for when an error occurs while updating a field.
        Creates the appropriate context for the model and calls the LLM to fix the error.

        Args:
            field_name (str): The name of the field to update in the artifact
            field_value (Any): The value to set the field to
            conversation (Conversation): The conversation object that contains the history of the conversation
            error (Exception): The error that occurred while updating the field

        Returns:
            tuple[bool, Any]: A tuple containing a boolean indicating success and the new field value if successful (if not, then None)
        """
        # Update the failed attempts for the field
        previous_attempts = self.failed_artifact_fields.get(field_name, [])
        previous_attempts, llm_formatted_attempts = update_attempts(
            error=error, attempt_id=str(field_value), previous_attempts=previous_attempts
        )
        self.failed_artifact_fields[field_name] = previous_attempts

        # Call the LLM to fix the error
        conversation_history_repr = conversation.get_repr_for_prompt(exclude_types=[ConversationMessageType.REASONING])
        artifact_schema_repr = self.get_schema_for_prompt(filter_one_field=field_name)
        result = await self._fix_artifact_error(
            field_name, llm_formatted_attempts, conversation_history_repr, artifact_schema_repr
        )

        # Handling the result of the LLM call
        if result["validation_result"] != ToolValidationResult.SUCCESS:
            return False, None
        # Only consider the first tool call
        tool_name = result["tool_names"][0]
        tool_args = result["tool_args_list"][0]
        if tool_name == f"{self.id}-{UPDATE_ARTIFACT_TOOL}":
            field_value = tool_args["value"]
            return True, field_value
        elif tool_name == f"{self.id}-{RESUME_CONV_TOOL}":
            return True, None

    def to_json(self) -> dict:
        artifact_fields = self.artifact.model_dump()
        return {
            "artifact": artifact_fields,
            "failed_fields": self.failed_artifact_fields,
        }

    @classmethod
    def from_json(
        cls,
        json_data: dict,
        kernel: Kernel,
        service_id: str,
        input_artifact: BaseModel,
        max_artifact_field_retries: int = 2,
    ) -> "Artifact":
        artifact = cls(kernel, service_id, input_artifact, max_artifact_field_retries)

        artifact.failed_artifact_fields = json_data["failed_fields"]

        # Iterate over artifact fields and set them to the values in the json data
        # Skip any fields that are set as "Unanswered"
        for field_name, field_value in json_data["artifact"].items():
            if field_value != "Unanswered":
                setattr(artifact.artifact, field_name, field_value)
        return artifact
