﻿// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Internal;

/// <summary>
/// Factory for creating <see cref="RunCreationOptions"/> definition.
/// </summary>
/// <remarks>
/// Improves testability.
/// </remarks>
internal static class AssistantRunOptionsFactory
{
    /// <summary>
    /// Produce <see cref="RunCreationOptions"/> by reconciling <see cref="OpenAIAssistantDefinition"/> and <see cref="OpenAIAssistantInvocationOptions"/>.
    /// </summary>
    /// <param name="definition">The assistant definition</param>
    /// <param name="invocationOptions">The run specific options</param>
    public static RunCreationOptions GenerateOptions(OpenAIAssistantDefinition definition, OpenAIAssistantInvocationOptions? invocationOptions)
    {
        int? truncationMessageCount = ResolveExecutionSetting(invocationOptions?.TruncationMessageCount, definition.ExecutionOptions?.TruncationMessageCount);

        RunCreationOptions options =
            new()
            {
                MaxCompletionTokens = ResolveExecutionSetting(invocationOptions?.MaxCompletionTokens, definition.ExecutionOptions?.MaxCompletionTokens),
                MaxPromptTokens = ResolveExecutionSetting(invocationOptions?.MaxPromptTokens, definition.ExecutionOptions?.MaxPromptTokens),
                ModelOverride = invocationOptions?.ModelName,
                NucleusSamplingFactor = ResolveExecutionSetting(invocationOptions?.TopP, definition.TopP),
                ParallelToolCallsEnabled = ResolveExecutionSetting(invocationOptions?.ParallelToolCallsEnabled, definition.ExecutionOptions?.ParallelToolCallsEnabled),
                ResponseFormat = ResolveExecutionSetting(invocationOptions?.EnableJsonResponse, definition.EnableJsonResponse) ?? false ? AssistantResponseFormat.JsonObject : null,
                Temperature = ResolveExecutionSetting(invocationOptions?.Temperature, definition.Temperature),
                TruncationStrategy = truncationMessageCount.HasValue ? RunTruncationStrategy.CreateLastMessagesStrategy(truncationMessageCount.Value) : null,
            };

        if (invocationOptions?.Metadata != null)
        {
            foreach (var metadata in invocationOptions.Metadata)
            {
                options.Metadata.Add(metadata.Key, metadata.Value ?? string.Empty);
            }
        }

        return options;
    }

    private static TValue? ResolveExecutionSetting<TValue>(TValue? setting, TValue? agentSetting) where TValue : struct
        =>
            setting.HasValue && (!agentSetting.HasValue || !EqualityComparer<TValue>.Default.Equals(setting.Value, agentSetting.Value)) ?
                setting.Value :
                null;
}
