// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Resources;

namespace PromptTemplates;

/// <summary>
/// This example demonstrates how to use ChatPrompt XML format with Audio content types.
/// The new ChatPrompt parser supports &lt;audio&gt; tags for various audio formats like WAV, MP3, etc.
/// </summary>
public class OpenAI_ChatPromptWithAudio(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Demonstrates using audio content in ChatPrompt XML format with data URI.
    /// </summary>
    [Fact]
    public async Task ChatPromptWithAudioContentDataUri()
    {
        // Load an audio file and convert to base64 data URI
        var audioBytes = await EmbeddedResource.ReadAllAsync("test_audio.wav");
        var audioBase64 = Convert.ToBase64String(audioBytes.ToArray());
        var dataUri = $"data:audio/wav;base64,{audioBase64}";

        var chatPrompt = $"""
            <message role="system">You are a helpful assistant that can analyze audio content.</message>
            <message role="user">
                <text>Please transcribe and analyze this audio file.</text>
                <audio>{dataUri}</audio>
            </message>
            """;

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o-audio-preview", // Use audio-capable model
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatFunction = kernel.CreateFunctionFromPrompt(chatPrompt);
        var result = await kernel.InvokeAsync(chatFunction);

        Console.WriteLine("=== ChatPrompt with Audio Content (Data URI) ===");
        Console.WriteLine("Prompt:");
        Console.WriteLine(chatPrompt);
        Console.WriteLine("\nResult:");
        Console.WriteLine(result);
    }

    /// <summary>
    /// Demonstrates a conversation flow using ChatPrompt with audio content across multiple messages.
    /// </summary>
    [Fact]
    public async Task ChatPromptConversationWithAudioContent()
    {
        var audioBytes = await EmbeddedResource.ReadAllAsync("test_audio.wav");
        var audioBase64 = Convert.ToBase64String(audioBytes.ToArray());
        var audioDataUri = $"data:audio/wav;base64,{audioBase64}";

        var chatPrompt = $"""
            <message role="system">You are a helpful assistant that specializes in audio analysis and transcription.</message>
            <message role="user">
                <text>I have an audio recording that I need help with. Can you analyze it?</text>
                <audio>{audioDataUri}</audio>
            </message>
            <message role="assistant">I can help you analyze this audio recording. Let me transcribe and examine its content for you. What specific information are you looking for from this audio?</message>
            <message role="user">
                <text>Can you provide a full transcription and also identify any background sounds or audio quality issues?</text>
            </message>
            """;

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o-audio-preview", // Use audio-capable model
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatFunction = kernel.CreateFunctionFromPrompt(chatPrompt);
        var result = await kernel.InvokeAsync(chatFunction);

        Console.WriteLine("=== ChatPrompt Conversation with Audio Content ===");
        Console.WriteLine("Prompt (showing conversation flow):");
        Console.WriteLine(chatPrompt[..Math.Min(800, chatPrompt.Length)] + "...");
        Console.WriteLine("\nResult:");
        Console.WriteLine(result);
    }
}
