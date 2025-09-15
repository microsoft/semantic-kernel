// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;
using Resources;

namespace ChatCompletion;

/// <summary>
/// These examples demonstrate how to use audio input and output with OpenAI Chat Completion
/// </summary>
/// <remarks>
/// Currently, audio input and output is only supported with the following models:
/// <list type="bullet">
/// <item>gpt-4o-audio-preview</item>
/// </list>
/// The sample demonstrates:
/// <list type="bullet">
/// <item>How to send audio input to the model</item>
/// <item>How to receive both text and audio output from the model</item>
/// <item>How to save and process the audio response</item>
/// </list>
/// </remarks>
public class OpenAI_ChatCompletionWithAudio(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This example demonstrates how to use audio input and receive both text and audio output from the model.
    /// </summary>
    /// <remarks>
    /// This sample shows:
    /// <list type="bullet">
    /// <item>Loading audio data from a resource file</item>
    /// <item>Configuring the chat completion service with audio options</item>
    /// <item>Enabling both text and audio response modalities</item>
    /// <item>Extracting and saving the audio response to a file</item>
    /// <item>Accessing the transcript metadata from the audio response</item>
    /// </list>
    /// </remarks>
    [Fact]
    public async Task UsingChatCompletionWithLocalInputAudioAndOutputAudio()
    {
        Console.WriteLine($"======== Open AI - {nameof(UsingChatCompletionWithLocalInputAudioAndOutputAudio)} ========\n");

        var audioBytes = await EmbeddedResource.ReadAllAsync("test_audio.wav");

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion("gpt-4o-audio-preview", TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var settings = new OpenAIPromptExecutionSettings
        {
            Audio = new ChatAudioOptions(ChatOutputAudioVoice.Shimmer, ChatOutputAudioFormat.Mp3),
            Modalities = ChatResponseModalities.Text | ChatResponseModalities.Audio
        };

        var chatHistory = new ChatHistory("You are a friendly assistant.");

        chatHistory.AddUserMessage([new AudioContent(audioBytes, "audio/wav")]);

        var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings);

        // Now we need to get the audio content from the result
        var audioReply = result.Items.First(i => i is AudioContent) as AudioContent;

        var currentDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)!;
        var audioFile = Path.Combine(currentDirectory, "audio_output.mp3");
        if (File.Exists(audioFile))
        {
            File.Delete(audioFile);
        }
        File.WriteAllBytes(audioFile, audioReply!.Data!.Value.ToArray());

        Console.WriteLine($"Generated audio: {new Uri(audioFile).AbsoluteUri}");
        Console.WriteLine($"Transcript: {audioReply.Metadata!["Transcript"]}");
    }

    /// <summary>
    /// This example demonstrates how to use audio input and receive only text output from the model.
    /// </summary>
    /// <remarks>
    /// This sample shows:
    /// <list type="bullet">
    /// <item>Loading audio data from a resource file</item>
    /// <item>Configuring the chat completion service with audio options</item>
    /// <item>Setting response modalities to Text only</item>
    /// <item>Processing the text response from the model</item>
    /// </list>
    /// </remarks>
    [Fact]
    public async Task UsingChatCompletionWithLocalInputAudioAndTextOutput()
    {
        Console.WriteLine($"======== Open AI - {nameof(UsingChatCompletionWithLocalInputAudioAndTextOutput)} ========\n");

        var audioBytes = await EmbeddedResource.ReadAllAsync("test_audio.wav");

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion("gpt-4o-audio-preview", TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var settings = new OpenAIPromptExecutionSettings
        {
            Audio = new ChatAudioOptions(ChatOutputAudioVoice.Shimmer, ChatOutputAudioFormat.Mp3),
            Modalities = ChatResponseModalities.Text
        };

        var chatHistory = new ChatHistory("You are a friendly assistant.");

        chatHistory.AddUserMessage([new AudioContent(audioBytes, "audio/wav")]);

        var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings);

        // Now we need to get the audio content from the result
        Console.WriteLine($"Assistant > {result}");
    }
}
