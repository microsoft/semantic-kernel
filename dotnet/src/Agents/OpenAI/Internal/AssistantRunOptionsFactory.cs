<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <param name="invocationOptions">The run specific options</param>
    public static RunCreationOptions GenerateOptions(OpenAIAssistantDefinition definition, OpenAIAssistantInvocationOptions? invocationOptions)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <param name="invocationOptions">The run specific options</param>
    public static RunCreationOptions GenerateOptions(OpenAIAssistantDefinition definition, OpenAIAssistantInvocationOptions? invocationOptions)
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    /// <param name="invocationOptions">The run specific options</param>
    public static RunCreationOptions GenerateOptions(OpenAIAssistantDefinition definition, OpenAIAssistantInvocationOptions? invocationOptions)
=======
>>>>>>> Stashed changes
=======
    /// <param name="invocationOptions">The run specific options</param>
    public static RunCreationOptions GenerateOptions(OpenAIAssistantDefinition definition, OpenAIAssistantInvocationOptions? invocationOptions)
=======
>>>>>>> Stashed changes
>>>>>>> head
    /// <param name="overrideInstructions">Instructions to use for the run</param>
    /// <param name="invocationOptions">The run specific options</param>
    public static RunCreationOptions GenerateOptions(OpenAIAssistantDefinition definition, string? overrideInstructions, OpenAIAssistantInvocationOptions? invocationOptions)
    /// <param name="invocationOptions">The run specific options</param>
    public static RunCreationOptions GenerateOptions(OpenAIAssistantDefinition definition, OpenAIAssistantInvocationOptions? invocationOptions)
    /// <param name="overrideInstructions">Instructions to use for the run</param>
    /// <param name="invocationOptions">The run specific options</param>
    public static RunCreationOptions GenerateOptions(OpenAIAssistantDefinition definition, string? overrideInstructions, OpenAIAssistantInvocationOptions? invocationOptions)
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    {
        int? truncationMessageCount = ResolveExecutionSetting(invocationOptions?.TruncationMessageCount, definition.ExecutionOptions?.TruncationMessageCount);

        RunCreationOptions options =
            new()
            {
                AdditionalInstructions = invocationOptions?.AdditionalInstructions ?? definition.ExecutionOptions?.AdditionalInstructions,
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                MaxCompletionTokens = ResolveExecutionSetting(invocationOptions?.MaxCompletionTokens, definition.ExecutionOptions?.MaxCompletionTokens),
                MaxPromptTokens = ResolveExecutionSetting(invocationOptions?.MaxPromptTokens, definition.ExecutionOptions?.MaxPromptTokens),
                ModelOverride = invocationOptions?.ModelName,
                NucleusSamplingFactor = ResolveExecutionSetting(invocationOptions?.TopP, definition.TopP),
                ParallelToolCallsEnabled = ResolveExecutionSetting(invocationOptions?.ParallelToolCallsEnabled, definition.ExecutionOptions?.ParallelToolCallsEnabled),
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                InstructionsOverride = overrideInstructions,
                MaxOutputTokenCount = ResolveExecutionSetting(invocationOptions?.MaxCompletionTokens, definition.ExecutionOptions?.MaxCompletionTokens),
                MaxInputTokenCount = ResolveExecutionSetting(invocationOptions?.MaxPromptTokens, definition.ExecutionOptions?.MaxPromptTokens),
                ModelOverride = invocationOptions?.ModelName,
                NucleusSamplingFactor = ResolveExecutionSetting(invocationOptions?.TopP, definition.TopP),
                AllowParallelToolCalls = ResolveExecutionSetting(invocationOptions?.ParallelToolCallsEnabled, definition.ExecutionOptions?.ParallelToolCallsEnabled),
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
