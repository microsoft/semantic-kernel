// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.Arguments.Extensions;

/// <summary>
/// Extensions for <see cref="KernelArguments"/>
/// </summary>
internal static class KernelArgumentsExtensions
{
    private static readonly Dictionary<string, PromptExecutionSettings> s_emptySettings = [];

    /// <summary>
    /// Provides a merged instance of <see cref="KernelArguments"/> with precedence for override arguments.
    /// </summary>
    /// <param name="primaryArguments">Primary arguments to merge. This is the base set of arguments.</param>
    /// <param name="overrideArguments">The override arguments.</param>
    /// <remarks>
    /// This merge preserves original <see cref="PromptExecutionSettings"/> and <see cref="KernelArguments"/> parameters.
    /// It allows for incremental addition or replacement of specific parameters while also preserving the ability
    /// to override the execution settings.
    /// </remarks>
    internal static KernelArguments Merge(this KernelArguments? primaryArguments, KernelArguments? overrideArguments)
    {
        // Avoid merge when override arguments are not set.
        if (overrideArguments is null)
        {
            return primaryArguments ?? [];
        }

        // Avoid merge when the Agent arguments are not set.
        if (primaryArguments is null)
        {
            return overrideArguments ?? [];
        }

        // Both instances are not null, merge with precedence for override arguments.

        // Merge execution settings with precedence for override arguments.
        Dictionary<string, PromptExecutionSettings>? settings =
            (overrideArguments.ExecutionSettings ?? s_emptySettings)
                .Concat(primaryArguments.ExecutionSettings ?? s_emptySettings)
                .GroupBy(entry => entry.Key)
                .ToDictionary(entry => entry.Key, entry => entry.First().Value);

        // Merge parameters with precedence for override arguments.
        Dictionary<string, object?>? parameters =
            overrideArguments
                .Concat(primaryArguments)
                .GroupBy(entry => entry.Key)
                .ToDictionary(entry => entry.Key, entry => entry.First().Value);

        return new KernelArguments(parameters, settings);
    }
}
