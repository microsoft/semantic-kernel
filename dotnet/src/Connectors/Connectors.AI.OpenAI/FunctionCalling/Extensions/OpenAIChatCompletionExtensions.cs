// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling.Extensions;

using System;
using System.Collections.Generic;
using System.Linq;
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
    /// <param name="callableFunctions"></param>
    /// <param name="functionCall"></param>
    /// <param name="cancellationToken">Async cancellation token</param>
    /// <remarks>This extension does not support multiple prompt results (Only the first will be returned)</remarks>
    /// <returns>Generated chat message in string format</returns>
    public static async Task<string> GenerateFunctionCallAsync(
        this IChatCompletion chatCompletion,
        ChatHistory chat,
        ChatRequestSettings requestSettings,
        IEnumerable<FunctionDefinition> callableFunctions,
        FunctionDefinition? functionCall = null,
        CancellationToken cancellationToken = default)
    {
        FunctionCallRequestSettings functionCallRequestSettings = requestSettings.ToFunctionCallRequestSettings(callableFunctions, functionCall ?? FunctionDefinition.Auto);
        IReadOnlyList<IChatResult>? chatResults = await chatCompletion.GetChatCompletionsAsync(chat, functionCallRequestSettings, cancellationToken).ConfigureAwait(false);
        var firstChatMessage = await chatResults[0].GetChatMessageAsync(cancellationToken).ConfigureAwait(false);
        return firstChatMessage.Content;
    }


    /// <summary>
    ///  Returns the content of the first result as a <typeparamref name="T"/> object.
    /// </summary>
    /// <param name="chatCompletion"></param>
    /// <param name="chat"></param>
    /// <param name="requestSettings"></param>
    /// <param name="options"></param>
    /// <param name="deserializationFallback"></param>
    /// <param name="cancellationToken"></param>
    /// <typeparam name="T"></typeparam>
    /// <returns></returns>
    public static async Task<T?> GenerateResponseAsync<T>(
        this IChatCompletion chatCompletion,
        ChatHistory chat,
        FunctionCallRequestSettings requestSettings,
        JsonSerializerOptions? options = null,
        Func<string, T>? deserializationFallback = null,
        CancellationToken cancellationToken = default)
    {
        IReadOnlyList<IChatResult>? chatResults = await chatCompletion.GetChatCompletionsAsync(chat, requestSettings, cancellationToken).ConfigureAwait(false);
        var firstChatMessage = await chatResults[0].GetChatMessageAsync(cancellationToken).ConfigureAwait(false);
        T? result = default;
        var firstElementJsonString = "";
        string content = firstChatMessage.Content;

        try
        {
            using var document = JsonDocument.Parse(content);

            var root = document.RootElement;

            var propertyEnumerator = root.EnumerateObject();

            if (propertyEnumerator.MoveNext())
            {
                var firstProperty = propertyEnumerator.Current.Value;
                firstElementJsonString = firstProperty.GetRawText().Trim();

                result = JsonSerializer.Deserialize<T>(firstElementJsonString, options ?? new JsonSerializerOptions(JsonSerializerDefaults.Web) { WriteIndented = true });
            }

        }

        catch (JsonException ex)
        {
            Console.WriteLine($"Error while converting '{firstElementJsonString}' to a '{typeof(T)}': {ex}");

            if (deserializationFallback != null)
            {
                result = deserializationFallback.Invoke(content);
            }
        }

        return result;
    }


    /// <summary>
    ///  Converts the <see cref="ChatRequestSettings"/> to <see cref="FunctionCallRequestSettings"/>
    /// </summary>
    /// <param name="settings"></param>
    /// <param name="callableFunctions"></param>
    /// <param name="targetFunctionCall"></param>
    /// <returns></returns>
    public static FunctionCallRequestSettings ToFunctionCallRequestSettings(this ChatRequestSettings settings, IEnumerable<FunctionDefinition> callableFunctions, FunctionDefinition? targetFunctionCall = null)
    {
        // Remove duplicates, if any, due to the inaccessibility of ReadOnlySkillCollection
        // Can't changes what skills are available to the context because you can't remove skills from the context
        List<FunctionDefinition> distinctCallableFunctions = callableFunctions
            .GroupBy(func => func.Name)
            .Select(group => group.First())
            .ToList();

        var requestSettings = new FunctionCallRequestSettings()
        {
            Temperature = settings.Temperature,
            TopP = settings.TopP,
            PresencePenalty = settings.PresencePenalty,
            FrequencyPenalty = settings.FrequencyPenalty,
            StopSequences = settings.StopSequences,
            MaxTokens = settings.MaxTokens,
            FunctionCall = targetFunctionCall ?? FunctionDefinition.Auto,
            CallableFunctions = distinctCallableFunctions
        };

        return requestSettings;
    }

}
