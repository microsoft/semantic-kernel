# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os
import tempfile

from semantic_kernel.agents import OpenAIResponsesAgent
from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.chat_history import ChatHistory

"""
The following sample demonstrates how to upload PDF and text files using BinaryContent
with an OpenAI Responses Agent. This shows how to create BinaryContent objects from files
and include them in conversations with the agent.

The sample demonstrates:
1. Creating BinaryContent from a PDF file
2. Creating BinaryContent from a text file  
3. Adding BinaryContent to chat history for agent consumption
4. Having the agent process and respond to questions about the uploaded files

Note: This sample uses the existing employees.pdf file from the resources directory.
"""

# Sample questions about the uploaded files
USER_INPUTS = [
    "What type of files did I upload?",
    "Can you tell me about the content in the PDF file?",
    "What does the text file contain?",
    "Summarize all the uploaded documents.",
]


def create_sample_text_content() -> str:
    """Create sample text content for demonstration."""
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
    # 1. Create the client using OpenAI resources and configuration
    client, model = OpenAIResponsesAgent.setup_resources()

    # 2. Get path to existing PDF file and create sample text file
    pdf_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "resources",
        "file_search",
        "employees.pdf",
    )

    # Create a sample text file for demonstration
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as text_file:
        text_content = create_sample_text_content()
        text_file.write(text_content)
        text_file_path = text_file.name

    try:
        # 3. Create BinaryContent objects from the files
        print("Creating BinaryContent from files...")

        # Create BinaryContent from PDF file
        pdf_binary_content = BinaryContent.from_file(file_path=pdf_file_path, mime_type="application/pdf")
        print(f"Created PDF BinaryContent: {pdf_binary_content.mime_type}, can_read: {pdf_binary_content.can_read}")

        # Create BinaryContent from text file
        text_binary_content = BinaryContent.from_file(file_path=text_file_path, mime_type="text/plain")
        print(f"Created text BinaryContent: {text_binary_content.mime_type}, can_read: {text_binary_content.can_read}")

        # Alternative: Create BinaryContent directly from data
        # You can also create BinaryContent directly from bytes or string data
        alternative_text_content = BinaryContent(
            data=text_content.encode("utf-8"), mime_type="text/plain", data_format="base64"
        )
        print(f"Alternative text BinaryContent: {alternative_text_content.mime_type}")

        # 4. Create a Semantic Kernel agent for the OpenAI Responses API
        agent = OpenAIResponsesAgent(
            ai_model_id=model,
            client=client,
            instructions=(
                "You are a helpful assistant that can analyze uploaded files. "
                "When users upload files, examine their content and provide helpful insights. "
                "You can identify file types, summarize content, and answer questions about the files."
            ),
            name="FileAnalyzer",
        )

        # 5. Create initial chat history with uploaded files
        chat_history = ChatHistory()

        # Add a message with the binary content attachments
        from semantic_kernel.contents.text_content import TextContent

        chat_history.add_user_message([
            TextContent(text="I'm uploading a PDF document and a text file for you to analyze."),
            pdf_binary_content,
            text_binary_content,
        ])

        # 6. Have a conversation with the agent about the uploaded files
        thread = None

        for user_input in USER_INPUTS:
            print(f"\n# User: '{user_input}'")

            # Get the agent's response using the user input
            first_chunk = True
            async for response in agent.invoke_stream(messages=user_input, thread=thread):
                thread = response.thread
                if first_chunk:
                    print(f"# {response.name}: ", end="", flush=True)
                    first_chunk = False
                print(response.content, end="", flush=True)
            print()  # New line after response

    finally:
        # 7. Clean up temporary text file (PDF file is permanent)
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
