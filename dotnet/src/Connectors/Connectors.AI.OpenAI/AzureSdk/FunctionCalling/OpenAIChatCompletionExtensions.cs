// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk.FunctionCalling;

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using SemanticKernel.AI.ChatCompletion;


/// <summary>
///  OpenAI chat completion extensions for function calling
/// </summary>
public static class OpenAIChatCompletionExtensions
{
    /// <summary>
    /// Generate a new chat message
    /// </summary>
    /// <param name="chatCompletion">Target interface to extend</param>
    /// <param name="chat">Chat history</param>
    /// <param name="requestSettings">AI request settings</param>
    /// <param name="functionCall"></param>
    /// <param name="functionCalls"></param>
    /// <param name="cancellationToken">Async cancellation token</param>
    /// <remarks>This extension does not support multiple prompt results (Only the first will be returned)</remarks>
    /// <returns>Generated chat message in string format</returns>
    public static async Task<string> GenerateMessageAsync(
        this IOpenAIChatCompletion chatCompletion,
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        FunctionDefinition? functionCall = null,
        FunctionDefinition[]? functionCalls = null,
        CancellationToken cancellationToken = default)
    {
        IReadOnlyList<IChatResult>? chatResults = await chatCompletion.GetChatCompletionsAsync(chat, requestSettings, functionCall, functionCalls, cancellationToken).ConfigureAwait(false);
        var firstChatMessage = await chatResults[0].GetChatMessageAsync(cancellationToken).ConfigureAwait(false);
        return firstChatMessage.Content;
    }


    /// <summary>
    ///  Returns the first result as a <typeparamref name="T"/> object.
    /// </summary>
    /// <param name="chatCompletion"></param>
    /// <param name="chat"></param>
    /// <param name="requestSettings"></param>
    /// <param name="functionCall"></param>
    /// <param name="functionCalls"></param>
    /// <param name="options"></param>
    /// <param name="cancellationToken"></param>
    /// <typeparam name="T"></typeparam>
    /// <returns></returns>
    public static async Task<T?> GenerateResponseAsync<T>(
        this IOpenAIChatCompletion chatCompletion,
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        FunctionDefinition? functionCall = null,
        FunctionDefinition[]? functionCalls = null,
        JsonSerializerOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        IReadOnlyList<IChatResult>? chatResults = await chatCompletion.GetChatCompletionsAsync(chat, requestSettings, functionCall, functionCalls, cancellationToken).ConfigureAwait(false);
        var firstChatMessage = await chatResults[0].GetChatMessageAsync(cancellationToken).ConfigureAwait(false);
        T? result = default;
        var firstElementJsonString = "";

        try
        {
            using var document = JsonDocument.Parse(firstChatMessage.Content);

            var root = document.RootElement;

            var propertyEnumerator = root.EnumerateObject();

            if (propertyEnumerator.MoveNext())
            {
                var firstProperty = propertyEnumerator.Current.Value;
                firstElementJsonString = firstProperty.GetRawText();

                result = JsonSerializer.Deserialize<T>(firstElementJsonString, options ?? new JsonSerializerOptions(JsonSerializerDefaults.Web) { WriteIndented = true });
            }

        }
        catch (JsonException ex)
        {
            Console.WriteLine($"Error while converting '{firstElementJsonString}' to a '{typeof(T)}': {ex}");
        }

        return result;
    }
}
