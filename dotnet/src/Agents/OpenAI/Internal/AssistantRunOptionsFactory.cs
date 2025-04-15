// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Internal;

/// <summary>
/// Factory for creating <see cref="RunCreationOptions"/> definition.
/// </summary>
internal static class AssistantRunOptionsFactory
{
    public static RunCreationOptions GenerateOptions(RunCreationOptions? defaultOptions, string? agentInstructions, RunCreationOptions? invocationOptions)
    {
        RunCreationOptions runOptions =
            new()
            {
                AdditionalInstructions = invocationOptions?.AdditionalInstructions ?? defaultOptions?.AdditionalInstructions,
                InstructionsOverride = invocationOptions?.InstructionsOverride ?? agentInstructions,
                MaxOutputTokenCount = invocationOptions?.MaxOutputTokenCount ?? defaultOptions?.MaxOutputTokenCount,
                MaxInputTokenCount = invocationOptions?.MaxInputTokenCount ?? defaultOptions?.MaxInputTokenCount,
                ModelOverride = invocationOptions?.ModelOverride ?? defaultOptions?.ModelOverride,
                NucleusSamplingFactor = invocationOptions?.NucleusSamplingFactor ?? defaultOptions?.NucleusSamplingFactor,
                AllowParallelToolCalls = invocationOptions?.AllowParallelToolCalls ?? defaultOptions?.AllowParallelToolCalls,
                ResponseFormat = invocationOptions?.ResponseFormat ?? defaultOptions?.ResponseFormat,
                Temperature = invocationOptions?.Temperature ?? defaultOptions?.Temperature,
                ToolConstraint = invocationOptions?.ToolConstraint ?? defaultOptions?.ToolConstraint,
                TruncationStrategy = invocationOptions?.TruncationStrategy ?? defaultOptions?.TruncationStrategy,
            };

        IList<ThreadInitializationMessage>? additionalMessages = invocationOptions?.AdditionalMessages ?? defaultOptions?.AdditionalMessages;
        if (additionalMessages != null)
        {
            runOptions.AdditionalMessages.AddRange(additionalMessages);
        }

        PopulateMetadata(defaultOptions, runOptions);
        PopulateMetadata(invocationOptions, runOptions);

        return runOptions;
    }

    private static void PopulateMetadata(RunCreationOptions? sourceOptions, RunCreationOptions targetOptions)
    {
        if (sourceOptions?.Metadata != null)
        {
            foreach (KeyValuePair<string, string> item in sourceOptions.Metadata)
            {
                targetOptions.Metadata[item.Key] = item.Value ?? string.Empty;
            }
        }
    }
}
