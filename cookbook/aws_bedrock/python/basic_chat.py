"""Basic chat example using AWS Bedrock with Semantic Kernel.

This example demonstrates how to:
1. Initialize a Semantic Kernel with AWS Bedrock
2. Create and manage a chat session
3. Handle conversation history
4. Interact with the LLM in a chat-like manner

Requirements:
    - AWS credentials configured
    - Access to AWS Bedrock service
    - Required packages: semantic-kernel, boto3

Example usage:
    python basic_chat.py
"""

import logging
import sys
from typing import Optional

import semantic_kernel as sk
from semantic_kernel.connectors.ai.bedrock import BedrockChatCompletion
from semantic_kernel.connectors.ai.bedrock.bedrock_config import BedrockConfig
from semantic_kernel.exceptions import ServiceInitializationError
from semantic_kernel.chat_models.chat_history import ChatHistory

from config import BEDROCK_SETTINGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def initialize_kernel() -> Optional[sk.Kernel]:
    """Initialize Semantic Kernel with AWS Bedrock.

    Returns:
        sk.Kernel: Initialized kernel with Bedrock chat service
        None: If initialization fails
    """
    try:
        kernel = sk.Kernel()

        # Configure Bedrock service
        config = BedrockConfig(
            model_id=BEDROCK_SETTINGS["model_id"],
            region=BEDROCK_SETTINGS["region"]
        )
        chat_service = BedrockChatCompletion(config)
        kernel.add_chat_service("bedrock", chat_service)

        logger.info(f"Initialized kernel with Bedrock model: {config.model_id}")
        return kernel

    except ServiceInitializationError as e:
        logger.error(f"Failed to initialize Bedrock service: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {str(e)}")
        return None

async def run_chat_session(kernel: sk.Kernel):
    """Run an interactive chat session with the model.

    Args:
        kernel: Initialized Semantic Kernel instance
    """
    print("\nWelcome to the Semantic Kernel + AWS Bedrock Chat!")
    print("Type 'exit' to end the conversation\n")

    chat_history = ChatHistory()

    try:
        while True:
            # Get user input
            user_input = input("User: ").strip()
            if not user_input or user_input.lower() == "exit":
                print("\nEnding chat session...")
                break

            # Add user message to history
            chat_history.add_user_message(user_input)

            try:
                # Get chat completion
                response = await kernel.chat_completion.complete_chat(
                    chat_history=chat_history
                )

                # Add assistant response to history
                chat_history.add_assistant_message(response)
                print(f"Assistant: {response}\n")

            except Exception as e:
                logger.error(f"Error during chat completion: {str(e)}")
                print("Sorry, I encountered an error processing your message. Please try again.")
                # Remove the failed interaction from history
                chat_history.messages.pop()

    except KeyboardInterrupt:
        print("\nChat session interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error in chat session: {str(e)}")
        print("\nAn unexpected error occurred. Please check the logs for details.")

async def main():
    """Main entry point for the chat application."""
    try:
        # Initialize the kernel
        kernel = await initialize_kernel()
        if not kernel:
            logger.error("Failed to initialize the kernel. Exiting...")
            sys.exit(1)

        # Run the chat session
        await run_chat_session(kernel)

    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())