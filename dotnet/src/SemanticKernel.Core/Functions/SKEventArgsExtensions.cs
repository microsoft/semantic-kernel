// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Events;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;

/// <summary>
/// SKEventArgs extensions
/// </summary>
public static class SKEventArgsExtensions
{
    /// <summary>
    /// Only tries to get the rendered prompt from the event args metadata if it exists.
    /// </summary>
    /// <param name="eventArgs">Target event args to extend</param>
    /// <param name="renderedPrompt">Outputs the renderedPrompt</param>
    /// <returns>True if the prompt was present</returns>
    public static bool TryGetRenderedPrompt(this SKEventArgs eventArgs, out string? renderedPrompt)
    {
        var found = eventArgs.Metadata.TryGetValue(SemanticFunction.RenderedPromptMetadataKey, out var renderedPromptObject);
        renderedPrompt = renderedPromptObject?.ToString();

        return found;
    }

    /// <summary>
    /// Only tries to update the prompt in the event args metadata if it exists.
    /// </summary>
    /// <param name="eventArgs">Target event args to extend</param>
    /// <param name="newPrompt">Prompt to override</param>
    /// <returns>True if the prompt exist and was updated</returns>
    public static bool TryUpdateRenderedPrompt(this SKEventArgs eventArgs, string newPrompt)
    {
        if (eventArgs.Metadata.ContainsKey(SemanticFunction.RenderedPromptMetadataKey))
        {
            eventArgs.Metadata[SemanticFunction.RenderedPromptMetadataKey] = newPrompt;
            return true;
        }

        return false;
    }
}
