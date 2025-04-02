---
title: Using OpenAI's Audio-Preview Model in Semantic Kernel
author: Your Name
date: April 15, 2025
---

![Audio Preview Model in Semantic Kernel](https://devblogs.microsoft.com/semantic-kernel/wp-content/uploads/sites/78/2025/04/audio-preview-blog.jpg)

OpenAI's **gpt-4o-audio-preview** is a powerful multimodal model that enables audio input and output capabilities, allowing developers to create more natural and accessible AI interactions. This model supports both speech-to-text and text-to-speech functionalities in a single API call through the Chat Completions API, making it suitable for building voice-enabled applications where turn-based interactions are appropriate.

In this post, we'll explore how to use the audio-preview model with Semantic Kernel in both C# and Python to create voice-enabled AI applications.

## Key Features of OpenAI's Audio-Preview Model with Chat Completions API

* **Multimodal Input/Output**: Process both text and audio inputs, and generate both text and audio outputs in a single API call.

* **Turn-Based Voice Interactions**: Suitable for non-real-time, turn-based conversational applications where each interaction is a complete request-response cycle.

* **Voice Synthesis Options**: Generate speech with support for multiple voices (like Alloy, Echo, Fable, Onyx, Nova, and Shimmer).

* **Audio Understanding**: Transcribe and comprehend spoken language from audio files.

* **Multilingual Support**: Process and generate audio in multiple languages, making it accessible to global users.

* **Integration with Function Calling**: Combine audio capabilities with function calling to create voice-controlled applications that can perform actions.

* **Simplified Development**: Single API for both audio input processing and audio output generation, reducing the complexity of building voice-enabled applications.

* **Batch Processing**: Well-suited for applications where complete audio messages are processed as discrete units rather than continuous streams.

**Note**: For truly low-latency, real-time voice interactions, OpenAI's Realtime API is the more appropriate choice. The Chat Completions API with audio capabilities is better suited for non-real-time applications where some latency is acceptable.

## Using Audio-Preview in Semantic Kernel

Semantic Kernel provides a straightforward way to integrate with OpenAI's audio-preview model. Let's see how to implement basic audio input and output functionality in both C# and Python.

### In .NET (C#)

For a C# project using Semantic Kernel, you can add the audio-preview model as an OpenAI chat completion service. Make sure you have your OpenAI API key (or Azure OpenAI endpoint and key if using Azure):

```csharp
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

// Initialize the OpenAI chat completion service with the audio-preview model
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion(
        modelId: "gpt-4o-audio-preview",
        apiKey: "YOUR_OPENAI_API_KEY"
    )
    .Build();

var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

// Configure settings for audio output
var settings = new OpenAIPromptExecutionSettings
{
    Audio = new ChatAudioOptions(
        ChatOutputAudioVoice.Shimmer, // Choose from available voices
        ChatOutputAudioFormat.Mp3     // Choose output format
    ),
    Modalities = ChatResponseModalities.Text | ChatResponseModalities.Audio // Request both text and audio
};

// Create a chat history and add an audio message
var chatHistory = new ChatHistory("You are a helpful assistant.");

// Add audio input (from a file or recorded audio)
byte[] audioBytes = File.ReadAllBytes("user_question.wav");
chatHistory.AddUserMessage([new AudioContent(audioBytes, "audio/wav")]);

// Get the model's response with both text and audio
var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings);

// Access the text response
Console.WriteLine($"Assistant > {result}");

// Access the audio response (if available)
if (result.Items.OfType<AudioContent>().Any())
{
    var audioContent = result.Items.OfType<AudioContent>().First();
    // Save or play the audio response
    File.WriteAllBytes("assistant_response.mp3", audioContent.Data.ToArray());
}
```

If you're using **Azure OpenAI**, the setup is similar – you would use `AzureOpenAIChatCompletionService` instead, providing your deployment name, endpoint, and API key.

### Python

Using the audio-preview model in Python with Semantic Kernel is equally straightforward:

```python
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory, AudioContent

async def main():
    # Initialize the kernel with OpenAI chat completion
    kernel = Kernel()
    chat_service = kernel.add_service(
        OpenAIChatCompletion(
            ai_model_id="gpt-4o-audio-preview",
            api_key="YOUR_OPENAI_API_KEY"
        )
    )

    # Create settings for audio output
    settings = {
        "audio": {
            "voice": "shimmer",
            "response_format": "mp3"
        },
        "modalities": ["text", "audio"]
    }

    # Start a chat history
    chat_history = ChatHistory()
    chat_history.add_system_message("You are a helpful assistant.")

    # Add audio input from a file
    with open("user_question.wav", "rb") as audio_file:
        audio_bytes = audio_file.read()

    audio_content = AudioContent.from_bytes(audio_bytes, mime_type="audio/wav")
    chat_history.add_user_message([audio_content])

    # Get the model's response
    response = await chat_service.chat_completion.get_chat_message_content(
        chat_history,
        settings=settings
    )

    # Access the text response
    print(f"Assistant > {response}")

    # Access the audio response (if available)
    audio_items = [item for item in response.items if isinstance(item, AudioContent)]
    if audio_items:
        audio_content = audio_items[0]
        # Save or play the audio response
        with open("assistant_response.mp3", "wb") as f:
            f.write(audio_content.data)

if __name__ == "__main__":
    asyncio.run(main())
```

## Building a Voice Chat Application

Semantic Kernel includes sample applications that demonstrate how to build voice-enabled chat applications. Let's look at a simple example that combines audio input and output for a complete voice conversation:

```python
import os
import asyncio
from semantic_kernel.contents import AudioContent, ChatHistory
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from audio_recorder import AudioRecorder
from audio_player import AudioPlayer

# File path for temporary audio storage
AUDIO_FILEPATH = os.path.join(os.path.dirname(__file__), "output.wav")

# Initialize services
chat_service = OpenAIChatCompletion(
    ai_model_id="gpt-4o-audio-preview",
    api_key="YOUR_OPENAI_API_KEY"
)

# Create chat history with system message
history = ChatHistory()
history.add_system_message("""
You are a helpful assistant. Respond to the user's questions
in a friendly and concise manner.
""")

async def chat_loop():
    print("Voice Chat Assistant (Press Ctrl+C to exit)")
    print("Press spacebar to start recording, release to send your message")

    try:
        while True:
            # Record user's audio input
            print("\nUser > ", end="", flush=True)
            with AudioRecorder(output_filepath=AUDIO_FILEPATH) as recorder:
                recorder.start_recording()

            # Convert audio to message and add to history
            audio_content = AudioContent.from_audio_file(AUDIO_FILEPATH)
            history.add_user_message([audio_content])

            # Get response from the model
            settings = {
                "audio": {"voice": "shimmer", "response_format": "mp3"},
                "modalities": ["text", "audio"]
            }
            response = await chat_service.get_chat_message_content(history, settings=settings)

            # Display text response
            print(f"\nAssistant > {response}")

            # Play audio response if available
            audio_items = [item for item in response.items if isinstance(item, AudioContent)]
            if audio_items:
                player = AudioPlayer(audio_content=audio_items[0])
                player.play()

            # Add assistant's response to history
            history.add_assistant_message(response)

    except KeyboardInterrupt:
        print("\nExiting chat...")

if __name__ == "__main__":
    asyncio.run(chat_loop())
```

This example creates a voice chat application where:

1. The user speaks into their microphone
2. The audio is sent to the model
3. The model processes the audio and generates both text and audio responses
4. The application displays the text and plays the audio response

## Real-time Audio Streaming with the Realtime API

For truly responsive, low-latency applications, Semantic Kernel supports real-time audio streaming through OpenAI's dedicated Realtime API (which is separate from the Chat Completions API we've been discussing). The Realtime API is specifically designed for applications requiring minimal latency and continuous audio streaming:

```python
from semantic_kernel.connectors.ai.open_ai import OpenAIRealtimeWebsocket
from semantic_kernel.contents import AudioContent
from audio_recorder_websocket import AudioRecorderWebsocket
from audio_player_websocket import AudioPlayerWebsocket

async def realtime_chat():
    # Configure settings for the session
    settings = {
        "model": "gpt-4o-audio-preview",
        "options": {
            "system_message": "You are a helpful assistant."
        }
    }

    # Initialize components
    realtime_client = OpenAIRealtimeWebsocket(settings=settings)
    audio_player = AudioPlayerWebsocket()
    audio_recorder = AudioRecorderWebsocket(realtime_client=realtime_client)

    # Start the session with all components
    async with audio_player, audio_recorder, realtime_client:
        async for event in realtime_client.receive():
            if event.event_type == "audio":
                # Stream audio to player
                await audio_player.add_audio(event.audio)
            elif event.event_type == "text":
                # Display transcribed text
                print(event.text.text, end="")

if __name__ == "__main__":
    asyncio.run(realtime_chat())
```

This real-time approach provides a much more natural conversation experience with minimal latency between user input and AI response. Unlike the Chat Completions API examples shown earlier, the Realtime API is specifically optimized for low-latency, continuous audio interactions where immediate responsiveness is critical.

## Conclusion

OpenAI's audio-preview model represents a significant advancement in creating more natural and accessible AI interactions. With Semantic Kernel's straightforward integration, developers can build voice-enabled applications that provide an enhanced user experience.

### Choosing the Right API for Your Use Case

* **Chat Completions API with audio-preview**: Best for turn-based interactions where complete audio messages are processed as discrete units. Suitable for applications like voice-based Q&A systems, audio transcription with AI responses, or asynchronous voice messaging where real-time interaction isn't critical.

* **Realtime API**: Ideal for applications requiring true low-latency, continuous audio streaming like virtual assistants, real-time language translation, or interactive voice response systems where immediate feedback is essential.

Whether you're building a voice assistant, a language learning application, or an accessibility tool, the combination of Semantic Kernel with the appropriate OpenAI audio API provides the foundation for creating powerful voice-enabled AI applications.

We encourage you to experiment with these capabilities in your own projects, carefully considering the interaction patterns and latency requirements of your specific use case. The ability to process and generate audio alongside text opens up new possibilities for how users can interact with AI systems, making them more intuitive and accessible to a wider audience.

## References

* [OpenAI Platform Documentation - Audio and Speech](https://platform.openai.com/docs/guides/audio)
* [OpenAI Realtime API Documentation](https://platform.openai.com/docs/guides/realtime)
* [Introducing the Realtime API | OpenAI](https://openai.com/index/introducing-the-realtime-api/)
* [Azure OpenAI Service Models](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)
* [Semantic Kernel Audio Concepts](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/concepts/audio)
* [Semantic Kernel Real-time Audio Examples](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/concepts/realtime)
