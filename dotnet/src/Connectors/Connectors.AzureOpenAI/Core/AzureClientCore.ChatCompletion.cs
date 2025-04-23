// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Diagnostics;
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
        options.ResponseModalities = ChatResponseModalities.Default;

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

        if (toolCallingConfig.Options?.AllowParallelCalls is not null)
        {
            options.AllowParallelToolCalls = toolCallingConfig.Options.AllowParallelCalls;
        }

        return options;
    }
}
