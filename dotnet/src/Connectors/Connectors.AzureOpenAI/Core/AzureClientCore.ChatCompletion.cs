// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;
using Azure.AI.OpenAI.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Diagnostics;
using OpenAI.Chat;

#pragma warning disable CA2208 // Instantiate argument exceptions correctly

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with Azure OpenAI services.
/// </summary>
internal partial class AzureClientCore
{
    /// <inheritdoc/>
    protected override OpenAIPromptExecutionSettings GetSpecializedExecutionSettings(PromptExecutionSettings? executionSettings)
        => AzureOpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);

    /// <inheritdoc/>
    protected override Activity? StartCompletionActivity(ChatHistory chatHistory, PromptExecutionSettings settings)
        => ModelDiagnostics.StartCompletionActivity(this.Endpoint, this.DeploymentName, ModelProvider, chatHistory, settings);

    /// <inheritdoc/>
    protected override ChatCompletionOptions CreateChatCompletionOptions(
        OpenAIPromptExecutionSettings executionSettings,
        ChatHistory chatHistory,
        ToolCallingConfig toolCallingConfig,
        Kernel? kernel)
    {
        if (executionSettings is not AzureOpenAIPromptExecutionSettings azureSettings)
        {
            return base.CreateChatCompletionOptions(executionSettings, chatHistory, toolCallingConfig, kernel);
        }
        ChatCompletionOptions options = ModelReaderWriter.Read<ChatCompletionOptions>(BinaryData.FromString("{\"stream_options\":{\"include_usage\":true}}")!)!;
        options.MaxOutputTokenCount = executionSettings.MaxTokens;
        options.Temperature = (float?)executionSettings.Temperature;
        options.TopP = (float?)executionSettings.TopP;
        options.FrequencyPenalty = (float?)executionSettings.FrequencyPenalty;
        options.PresencePenalty = (float?)executionSettings.PresencePenalty;
#pragma warning disable OPENAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

        options.Seed = executionSettings.Seed;
#pragma warning restore OPENAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        options.EndUserId = executionSettings.User;
        options.TopLogProbabilityCount = executionSettings.TopLogprobs;
        options.IncludeLogProbabilities = executionSettings.Logprobs;
        options.StoredOutputEnabled = executionSettings.Store;
        options.ReasoningEffortLevel = GetEffortLevel(executionSettings);

        if (executionSettings.Modalities is not null)
        {
            options.ResponseModalities = GetResponseModalities(executionSettings);
        }

        if (executionSettings.Audio is not null)
        {
            options.AudioOptions = GetAudioOptions(executionSettings);
        }

        if (azureSettings.SetNewMaxCompletionTokensEnabled)
        {
#pragma warning disable AOAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
            options.SetNewMaxCompletionTokensPropertyEnabled(true);
#pragma warning restore AOAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        }

        if (azureSettings.UserSecurityContext is not null)
        {
#pragma warning disable AOAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
            options.SetUserSecurityContext(azureSettings.UserSecurityContext);
#pragma warning restore AOAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        }

        var responseFormat = GetResponseFormat(executionSettings);
        if (responseFormat is not null)
        {
            options.ResponseFormat = responseFormat;
        }

        if (toolCallingConfig.Choice is not null)
        {
            options.ToolChoice = toolCallingConfig.Choice;
        }

        if (toolCallingConfig.Tools is { Count: > 0 } tools)
        {
            options.Tools.AddRange(tools);
        }

        if (azureSettings.AzureChatDataSource is not null)
        {
#pragma warning disable AOAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
            options.AddDataSource(azureSettings.AzureChatDataSource);
#pragma warning restore AOAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        }

        if (toolCallingConfig.Options?.AllowParallelCalls is not null)
        {
            options.AllowParallelToolCalls = toolCallingConfig.Options.AllowParallelCalls;
        }

        if (executionSettings.TokenSelectionBiases is not null)
        {
            foreach (var keyValue in executionSettings.TokenSelectionBiases)
            {
                options.LogitBiases.Add(keyValue.Key, keyValue.Value);
            }
        }

        if (executionSettings.StopSequences is { Count: > 0 })
        {
            foreach (var s in executionSettings.StopSequences)
            {
                options.StopSequences.Add(s);
            }
        }

        if (executionSettings.Metadata is not null)
        {
            foreach (var kvp in executionSettings.Metadata)
            {
                options.Metadata.Add(kvp.Key, kvp.Value);
            }
        }

        return options;
    }

    /// <summary>
    /// Gets the response modalities from the execution settings.
    /// </summary>
    /// <param name="executionSettings">The execution settings.</param>
    /// <returns>The response modalities as a <see cref="ChatResponseModalities"/> flags enum.</returns>
    private static ChatResponseModalities GetResponseModalities(OpenAIPromptExecutionSettings executionSettings)
    {
        static ChatResponseModalities ParseResponseModalitiesEnumerable(IEnumerable<string> responseModalitiesStrings)
        {
            ChatResponseModalities result = ChatResponseModalities.Default;
            foreach (var modalityString in responseModalitiesStrings)
            {
                if (Enum.TryParse<ChatResponseModalities>(modalityString, true, out var parsedModality))
                {
                    result |= parsedModality;
                }
                else
                {
                    throw new NotSupportedException($"The provided response modalities '{modalityString}' is not supported.");
                }
            }

            return result;
        }

        if (executionSettings.Modalities is null)
        {
            return ChatResponseModalities.Default;
        }

        if (executionSettings.Modalities is ChatResponseModalities responseModalities)
        {
            return responseModalities;
        }

        if (executionSettings.Modalities is IEnumerable<string> responseModalitiesStrings)
        {
            return ParseResponseModalitiesEnumerable(responseModalitiesStrings);
        }

        if (executionSettings.Modalities is string responseModalitiesString)
        {
            if (Enum.TryParse<ChatResponseModalities>(responseModalitiesString, true, out var parsedResponseModalities))
            {
                return parsedResponseModalities;
            }
            throw new NotSupportedException($"The provided response modalities '{responseModalitiesString}' is not supported.");
        }

        if (executionSettings.Modalities is JsonElement responseModalitiesElement)
        {
            if (responseModalitiesElement.ValueKind == JsonValueKind.String)
            {
                var modalityString = responseModalitiesElement.GetString();
                if (Enum.TryParse<ChatResponseModalities>(modalityString, true, out var parsedResponseModalities))
                {
                    return parsedResponseModalities;
                }

                throw new NotSupportedException($"The provided response modalities '{modalityString}' is not supported.");
            }

            if (responseModalitiesElement.ValueKind == JsonValueKind.Array)
            {
                try
                {
                    var modalitiesEnumeration = JsonSerializer.Deserialize<IEnumerable<string>>(responseModalitiesElement.GetRawText())!;
                    return ParseResponseModalitiesEnumerable(modalitiesEnumeration);
                }
                catch (JsonException ex)
                {
                    throw new NotSupportedException("The provided response modalities JSON array may only contain strings.", ex);
                }
            }

            throw new NotSupportedException($"The provided response modalities '{executionSettings.Modalities?.GetType()}' is not supported.");
        }

        return ChatResponseModalities.Default;
    }


    /// <summary>
    /// Gets the audio options from the execution settings.
    /// </summary>
    /// <param name="executionSettings">The execution settings.</param>
    /// <returns>The audio options as a <see cref="ChatAudioOptions"/> object.</returns>
    private static ChatAudioOptions GetAudioOptions(OpenAIPromptExecutionSettings executionSettings)
    {
        if (executionSettings.Audio is ChatAudioOptions audioOptions)
        {
            return audioOptions;
        }

        if (executionSettings.Audio is JsonElement audioOptionsElement)
        {
            try
            {
                var result = ModelReaderWriter.Read<ChatAudioOptions>(BinaryData.FromString(audioOptionsElement.GetRawText()));
                if (result != null)
                {
                    return result;
                }
            }
            catch (Exception ex)
            {
                throw new NotSupportedException($"Failed to parse the provided audio options from JSON. Ensure the JSON structure matches ChatAudioOptions format.", ex);
            }
        }

        if (executionSettings.Audio is string audioOptionsString)
        {
            try
            {
                var result = ModelReaderWriter.Read<ChatAudioOptions>(BinaryData.FromString(audioOptionsString));
                if (result != null)
                {
                    return result;
                }
            }
            catch (Exception ex)
            {
                throw new NotSupportedException($"Failed to parse the provided audio options from string. Ensure the string is valid JSON that matches ChatAudioOptions format.", ex);
            }
        }

        throw new NotSupportedException($"The provided audio options '{executionSettings.Audio?.GetType()}' is not supported.");
    }
}
