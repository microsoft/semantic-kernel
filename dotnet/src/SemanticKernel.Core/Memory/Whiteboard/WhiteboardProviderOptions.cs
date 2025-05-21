// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Options for configuring the <see cref="WhiteboardProvider"/>.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class WhiteboardProviderOptions
{
    /// <summary>
    /// Gets or sets the maximum number of messages to keep on the whiteboard.
    /// </summary>
    /// <value>
    /// Defaults to 10 if not specified.
    /// </value>
    public int? MaxWhiteboardMessages { get; set; }

    /// <summary>
    /// Gets or sets a string that is prefixed to the messages on the whiteboard,
    /// when providing them as context to the AI model.
    /// </summary>
    /// <value>
    /// Defaults to &quot;## Whiteboard\nThe following list of messages are currently on the whiteboard:&quot;
    /// </value>
    public string? ContextPrompt { get; init; }

    /// <summary>
    /// Gets or sets the message to provide to the AI model when there are no messages on the whiteboard.
    /// </summary>
    /// <value>
    /// Defaults to &quot;## Whiteboard\nThe whiteboard is currently empty.&quot;
    /// </value>
    public string? WhiteboardEmptyPrompt { get; init; }

    /// <summary>
    /// Gets or sets a prompt template to use to update the whiteboard with the latest messages
    /// if the built-in prompt needs to be customized.
    /// </summary>
    /// <remarks>
    /// The following parameters can be used in the prompt:
    /// {{$maxWhiteboardMessages}}
    /// {{$inputMessages}}
    /// {{$currentWhiteboard}}
    /// </remarks>
    public string? MaintenancePromptTemplate { get; init; }
}
