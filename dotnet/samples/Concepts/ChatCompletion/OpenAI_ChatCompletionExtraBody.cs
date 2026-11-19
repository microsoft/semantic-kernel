// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;

#pragma warning disable SKEXP0010 // OpenAIPromptExecutionSettings.ExtraBody is experimental.

/// <summary>
/// <see cref="OpenAIPromptExecutionSettings.ExtraBody"/> is an escape hatch that injects additional fields
/// into the request body sent to the OpenAI-compatible endpoint. Use it to pass vendor-specific or preview
/// parameters that are not modeled by <see cref="OpenAIPromptExecutionSettings"/> (for example,
/// Qwen3's <c>enable_thinking</c> flag, ChatGLM thinking modes, or NVIDIA NIM custom knobs).
///
/// <para>Key syntax:</para>
/// <list type="bullet">
/// <item><description>A plain key (without leading <c>$.</c>) is treated as a literal top-level field name.</description></item>
/// <item><description>A key starting with <c>$.</c> is interpreted as a JSONPath expression and applied as a deep patch onto the request body.</description></item>
/// </list>
/// </summary>
public class OpenAI_ChatCompletionExtraBody(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Adds a flat top-level field to the outgoing chat completion request:
    /// <code>{ "messages": [...], "model": "qwen-plus", "enable_thinking": false, ... }</code>
    /// </summary>
    [Fact]
    public async Task FlatFieldExampleAsync()
    {
        OpenAIChatCompletionService chatCompletionService = new(
            TestConfiguration.OpenAI.ChatModelId,
            TestConfiguration.OpenAI.ApiKey);

        var settings = new OpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?>
            {
                // Required by Qwen3 open-source models for non-streaming calls.
                ["enable_thinking"] = false,
            },
        };

        var chatHistory = new ChatHistory("You are a helpful assistant.");
        chatHistory.AddUserMessage("Who are you?");

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings);

        Console.WriteLine(reply.Content);
    }

    /// <summary>
    /// Uses a <c>$.</c>-prefixed JSONPath key to surgically patch a nested field in the request body
    /// (for example, into <c>thinking.enabled</c>). This avoids having to specify the entire nested object.
    /// </summary>
    [Fact]
    public async Task DeepPatchExampleAsync()
    {
        OpenAIChatCompletionService chatCompletionService = new(
            TestConfiguration.OpenAI.ChatModelId,
            TestConfiguration.OpenAI.ApiKey);

        var settings = new OpenAIPromptExecutionSettings
        {
            ExtraBody = new Dictionary<string, object?>
            {
                // Emits { "thinking": { "enabled": false } } in the request body.
                ["$.thinking.enabled"] = false,
            },
        };

        var chatHistory = new ChatHistory("You are a helpful assistant.");
        chatHistory.AddUserMessage("Summarize the plot of Hamlet in one sentence.");

        var reply = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings);

        Console.WriteLine(reply.Content);
    }
}
