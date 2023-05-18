//Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers;
using Microsoft.SemanticKernel.Orchestration;

namespace SemanticKernel.Service.CopilotChat.Skills;

/// <summary>
/// Utility methods for skills.
/// </summary>
internal static class Utilities
{
    /// <summary>
    /// Creates a new context with a clone of the variables from the given context.
    /// This is useful when you want to modify the variables in a context without
    /// affecting the original context.
    /// </summary>
    /// <param name="context">The context to copy.</param>
    /// <returns>A new context with a clone of the variables.</returns>
    internal static SKContext CopyContextWithVariablesClone(SKContext context)
        => new(
            context.Variables.Clone(),
            context.Memory,
            context.Skills,
            context.Log,
            context.CancellationToken);

    /// <summary>
    /// Calculate the number of tokens in a string.
    /// </summary>
    internal static int TokenCount(string text) => GPT3Tokenizer.Encode(text).Count;
}
