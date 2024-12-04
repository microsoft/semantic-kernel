// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel.ChatCompletion;
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
    /// <param name="overrideInstructions">Instructions to use for the run</param>
    /// <param name="invocationOptions">The run specific options</param>
    public static RunCreationOptions GenerateOptions(OpenAIAssistantDefinition definition, string? overrideInstructions, OpenAIAssistantInvocationOptions? invocationOptions)
    {
        int? truncationMessageCount = ResolveExecutionSetting(invocationOptions?.TruncationMessageCount, definition.ExecutionOptions?.TruncationMessageCount);

        RunCreationOptions options =
            new()
            {
                AdditionalInstructions = invocationOptions?.AdditionalInstructions ?? definition.ExecutionOptions?.AdditionalInstructions,
                InstructionsOverride = overrideInstructions,
                MaxOutputTokenCount = ResolveExecutionSetting(invocationOptions?.MaxCompletionTokens, definition.ExecutionOptions?.MaxCompletionTokens),
                MaxInputTokenCount = ResolveExecutionSetting(invocationOptions?.MaxPromptTokens, definition.ExecutionOptions?.MaxPromptTokens),
                ModelOverride = invocationOptions?.ModelName,
                NucleusSamplingFactor = ResolveExecutionSetting(invocationOptions?.TopP, definition.TopP),
                AllowParallelToolCalls = ResolveExecutionSetting(invocationOptions?.ParallelToolCallsEnabled, definition.ExecutionOptions?.ParallelToolCallsEnabled),
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

        if (invocationOptions?.AdditionalMessages != null)
        {
            foreach (ChatMessageContent message in invocationOptions.AdditionalMessages)
            {
                ThreadInitializationMessage threadMessage = new(
                    role: message.Role == AuthorRole.User ? MessageRole.User : MessageRole.Assistant,
                    content: AssistantMessageFactory.GetMessageContents(message));

                options.AdditionalMessages.Add(threadMessage);
            }
        }

        return options;
    }

    private static TValue? ResolveExecutionSetting<TValue>(TValue? setting, TValue? agentSetting) where TValue : struct
        =>
            setting.HasValue && (!agentSetting.HasValue || !EqualityComparer<TValue>.Default.Equals(setting.Value, agentSetting.Value)) ?
                setting.Value :
                agentSetting;
}
