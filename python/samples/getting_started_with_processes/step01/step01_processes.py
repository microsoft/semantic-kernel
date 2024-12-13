# Copyright (c) Microsoft. All rights reserved.

import asyncio
from enum import Enum
from typing import ClassVar

from pydantic import Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.processes.process_builder import ProcessBuilder


class CommonEvents(Enum):
    UserInputReceived = "UserInputReceived"
    AssistantResponseGenerated = "AssistantResponseGenerated"


class ChatBotEvents(Enum):
    StartProcess = "startProcess"
    IntroComplete = "introComplete"
    AssistantResponseGenerated = "assistantResponseGenerated"
    Exit = "exit"


class UserInputState(KernelBaseModel):
    user_inputs: list[str] = []
    current_input_index: int = 0


class UserInputStep(KernelProcessStep[UserInputState]):
    GET_USER_INPUT: ClassVar[str] = "get_user_input"

    def create_default_state(self) -> "UserInputState":
        """Creates the default UserInputState."""
        return UserInputState()

    def populate_user_inputs(self):
        """Method to be overridden by the user to populate with custom user messages."""
        pass

    async def activate(self, state: KernelProcessStepState[UserInputState]):
        """Activates the step and sets the state."""
        state.state = state.state or self.create_default_state()
        self.state = state.state
        self.populate_user_inputs()

    @kernel_function(name=GET_USER_INPUT)
    async def get_user_input(self, context: KernelProcessStepContext):
        """Gets the user input."""
        if not self.state:
            raise ValueError("State has not been initialized")

        user_message = input("USER: ")

        # print(f"USER: {user_message}")

        if "exit" in user_message:
            await context.emit_event(process_event=ChatBotEvents.Exit, data=None)
            return

        self.state.current_input_index += 1

        # Emit the user input event
        await context.emit_event(process_event=CommonEvents.UserInputReceived, data=user_message)


class ScriptedInputStep(UserInputStep):
    def populate_user_inputs(self):
        """Override the method to populate user inputs for the chat step."""
        if self.state is not None:
            self.state.user_inputs.append("Hello")
            self.state.user_inputs.append("How tall is the tallest mountain?")
            self.state.user_inputs.append("How low is the lowest valley?")
            self.state.user_inputs.append("How wide is the widest river?")
            self.state.user_inputs.append("exit")

    @kernel_function
    async def get_user_input(self, context: KernelProcessStepContext):
        """Gets the user input."""
        if not self.state:
            raise ValueError("State has not been initialized")

        user_message = self.state.user_inputs[self.state.current_input_index]

        print(f"USER: {user_message}")

        if "exit" in user_message:
            await context.emit_event(process_event=ChatBotEvents.Exit, data=None)
            return

        self.state.current_input_index += 1

        # Emit the user input event
        await context.emit_event(process_event=CommonEvents.UserInputReceived, data=user_message)


class IntroStep(KernelProcessStep):
    @kernel_function
    async def print_intro_message(self):
        print("Welcome to Processes in Semantic Kernel.\n")


class ChatBotState(KernelBaseModel):
    """The state object for ChatBotResponseStep."""

    chat_messages: list = []


SERVICE_ID = "default"


class ChatBotResponseStep(KernelProcessStep[ChatBotState]):
    GET_CHAT_RESPONSE: ClassVar[str] = "get_chat_response"

    state: ChatBotState = Field(default_factory=ChatBotState)

    async def activate(self, state: "KernelProcessStepState[ChatBotState]"):
        """Activates the step and initializes the state object."""
        self.state = state.state or ChatBotState()
        self.state.chat_messages = self.state.chat_messages or []

    @kernel_function(name=GET_CHAT_RESPONSE)
    async def get_chat_response(self, context: "KernelProcessStepContext", user_message: str, kernel: "Kernel"):
        """Generates a response from the chat completion service."""
        # Add user message to the state
        self.state.chat_messages.append({"role": "user", "message": user_message})

        # Get chat completion service and generate a response
        chat_service: ChatCompletionClientBase = kernel.get_service(service_id=SERVICE_ID)
        settings = chat_service.instantiate_prompt_execution_settings(service_id=SERVICE_ID)

        chat_history = ChatHistory()
        chat_history.add_user_message(user_message)
        response = await chat_service.get_chat_message_contents(chat_history=chat_history, settings=settings)

        if response is None:
            raise ValueError("Failed to get a response from the chat completion service.")

        answer = response[0].content

        print(f"ASSISTANT: {answer}")

        # Update state with the response
        self.state.chat_messages.append(answer)

        # Emit an event: assistantResponse
        await context.emit_event(process_event=ChatBotEvents.AssistantResponseGenerated, data=answer)


kernel = Kernel()


async def step01_processes(scripted: bool = True):
    kernel.add_service(OpenAIChatCompletion(service_id="default"))

    process = ProcessBuilder(name="ChatBot")

    # Define the steps on the process builder based on their types, not concrete objects
    intro_step = process.add_step(IntroStep)
    user_input_step = process.add_step(ScriptedInputStep if scripted else UserInputStep)
    response_step = process.add_step(ChatBotResponseStep)

    # Define the input event that starts the process and where to send it
    process.on_input_event(event_id=ChatBotEvents.StartProcess).send_event_to(target=intro_step)

    # Define the event that triggers the next step in the process
    intro_step.on_function_result(function_name=IntroStep.print_intro_message.__name__).send_event_to(
        target=user_input_step
    )

    # Define the event that triggers the process to stop
    user_input_step.on_event(event_id=ChatBotEvents.Exit).stop_process()
    # For the user step, send the user input to the response step
    user_input_step.on_event(event_id=CommonEvents.UserInputReceived).send_event_to(
        target=response_step, parameter_name="user_message"
    )

    # For the response step, send the response back to the user input step
    response_step.on_event(event_id=ChatBotEvents.AssistantResponseGenerated).send_event_to(target=user_input_step)

    # Build the kernel process
    kernel_process = process.build()

    # Start the process
    await start(
        process=kernel_process,
        kernel=kernel,
        initial_event=KernelProcessEvent(id=ChatBotEvents.StartProcess, data=None),
    )


if __name__ == "__main__":
    # if you want to run this sample with your won input, set the below parameter to False
    asyncio.run(step01_processes(scripted=False))
