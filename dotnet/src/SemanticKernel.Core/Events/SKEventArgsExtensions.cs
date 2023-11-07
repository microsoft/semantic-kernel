// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// SKEventArgs extensions
/// </summary>
public static class SKEventArgsExtensions
{
    /// <summary>
    /// Metadata key for storing the rendered prompt when available.
    /// </summary>
    public const string RenderedPromptMetadataKey = "RenderedPrompt";

    /// <summary>
    /// Only tries to get the rendered prompt from the event args metadata if it exists.
    /// </summary>
    /// <param name="eventArgs">Target event args to extend</param>
    /// <param name="renderedPrompt">Outputs the renderedPrompt</param>
    /// <returns>True if the prompt was present</returns>
    public static bool TryGetRenderedPrompt(this SKEventArgs eventArgs, out string? renderedPrompt)
    {
        var found = eventArgs.Metadata.TryGetValue(SKEventArgsExtensions.RenderedPromptMetadataKey, out var renderedPromptObject);
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
        if (eventArgs.Metadata.ContainsKey(SKEventArgsExtensions.RenderedPromptMetadataKey))
        {
            eventArgs.Metadata[SKEventArgsExtensions.RenderedPromptMetadataKey] = newPrompt;
            return true;
        }

        return false;
    }
}
