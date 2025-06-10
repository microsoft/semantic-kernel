# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os
import tempfile

from semantic_kernel.agents import OpenAIResponsesAgent
from semantic_kernel.connectors.ai.open_ai import OpenAISettings
from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole

"""
The following sample demonstrates how to upload PDF and text files using BinaryContent
with an OpenAI Responses Agent. This shows how to create BinaryContent objects from files
and compose multi-modal messages that combine text and binary content.

The sample demonstrates:
1. Creating BinaryContent from a PDF file
2. Creating BinaryContent from a text file
3. Composing multi-modal messages with mixed content types (text + binary)
4. Sending complex messages directly to the agent via the messages parameter
5. Having the agent process and respond to questions about the uploaded files

This approach differs from simple string-based interactions by showing how to combine
multiple content types within a single message, which is useful for rich media interactions.

Note: This sample uses the existing employees.pdf file from the resources directory.
"""

# Sample follow-up questions to demonstrate continued conversation
USER_INPUTS = [
    "What specific types of files did I just upload?",
    "Can you tell me about the content in the PDF file?",
    "What does the text file contain?",
    "Can you provide a summary of both documents?",
]


def create_sample_text_content() -> str:
    """Create sample text content for demonstration purposes.

    Returns:
        str: A sample company policy document in text format.
    """
    return """Company Policy Document - Remote Work Guidelines

This document outlines our company's remote work policies and procedures.

Remote Work Eligibility:
- Full-time employees with at least 6 months tenure
- Managers approval required
- Home office setup must meet security requirements

Work Schedule:
- Core hours: 10 AM - 3 PM local time
- Flexible start/end times outside core hours
- Maximum 3 remote days per week for hybrid roles

Communication Requirements:
- Daily check-ins with team lead
- Weekly video conference participation
- Response time: within 4 hours during business hours

Equipment and Security:
- Company-provided laptop and VPN access
- Secure Wi-Fi connection required
- No public Wi-Fi for work activities

For questions about remote work policies, contact HR at hr@company.com
"""


async def main():
    # 1. Initialize the OpenAI client
    client = OpenAIResponsesAgent.create_client()

    # 2. Prepare file paths and create sample content
    pdf_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "resources",
        "file_search",
        "employees.pdf",
    )

    # Create a temporary text file for demonstration purposes
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as text_file:
        text_content = create_sample_text_content()
        text_file.write(text_content)
        text_file_path = text_file.name

    try:
        # 3. Create BinaryContent objects from files using different methods
        print("Creating BinaryContent from files...")

        # Method 1: Create BinaryContent from an existing PDF file
        pdf_binary_content = BinaryContent.from_file(file_path=pdf_file_path, mime_type="application/pdf")
        print(f"Created PDF BinaryContent: {pdf_binary_content.mime_type}, can_read: {pdf_binary_content.can_read}")

        # Method 2: Create BinaryContent from the temporary text file
        text_binary_content = BinaryContent.from_file(file_path=text_file_path, mime_type="text/plain")
        print(f"Created text BinaryContent: {text_binary_content.mime_type}, can_read: {text_binary_content.can_read}")

        # Method 3: Create BinaryContent directly from in-memory data
        # This approach allows creating BinaryContent without file I/O operations
        alternative_text_content = BinaryContent(
            data=text_content.encode("utf-8"), mime_type="text/plain", data_format="base64"
        )
        print(f"Alternative text BinaryContent: {alternative_text_content.mime_type}")

        # 4. Initialize the OpenAI Responses Agent with file analysis capabilities
        # Configure the AI model for responses
        settings = OpenAISettings()
        responses_model = settings.responses_model_id or "gpt-4o"

        agent = OpenAIResponsesAgent(
            ai_model_id=responses_model,
            client=client,
            instructions=(
                "You are a helpful assistant that can analyze uploaded files. "
                "When users upload files, examine their content and provide helpful insights. "
                "You can identify file types, summarize content, and answer questions about the files."
            ),
            name="FileAnalyzer",
        )

        # 5. Demonstrate multi-modal message composition
        # This showcases combining text and binary content in a single message

        # Compose a message containing both text instructions and file attachments
        # This pattern is ideal for scenarios requiring rich, mixed-content interactions
        initial_message = ChatMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="I'm uploading a PDF document and a text file for you to analyze."),
                pdf_binary_content,
                text_binary_content,
            ],
        )

        # 6. Conduct a conversation with the agent about the uploaded files
        thread = None

        # Send the initial multi-modal message containing file uploads
        print("\n# User: 'I'm uploading a PDF document and a text file for you to analyze.'")
        first_chunk = True
        async for response in agent.invoke_stream(messages=initial_message, thread=thread):
            thread = response.thread
            if first_chunk:
                print(f"# {response.name}: ", end="", flush=True)
                first_chunk = False
            print(response.content, end="", flush=True)
        print()  # New line after response

        # Continue the conversation with text-based follow-up questions
        for user_input in USER_INPUTS:
            print(f"\n# User: '{user_input}'")

            # Process follow-up questions using standard text input
            first_chunk = True
            async for response in agent.invoke_stream(messages=user_input, thread=thread):
                thread = response.thread
                if first_chunk:
                    print(f"# {response.name}: ", end="", flush=True)
                    first_chunk = False
                print(response.content, end="", flush=True)
            print()  # New line after response

    finally:
        # 7. Clean up temporary resources
        if os.path.exists(text_file_path):
            os.unlink(text_file_path)

    print("\n" + "=" * 60)
    print("Sample completed!")
    print("\nKey points about BinaryContent:")
    print("1. Use BinaryContent.from_file() to create from existing files")
    print("2. Use BinaryContent(data=...) to create from bytes/string data")
    print("3. Specify appropriate mime_type for proper handling")
    print("4. BinaryContent can be included in chat messages alongside text")
    print("5. The OpenAI Responses API will process supported file types")
    print("\nSupported file types include:")
    print("- PDF documents (application/pdf)")
    print("- Text files (text/plain)")


if __name__ == "__main__":
    asyncio.run(main())
