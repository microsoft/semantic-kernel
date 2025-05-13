// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Options for configuring the <see cref="WhiteboardBehavior"/>.
/// </summary>
[Experimental("SKEXP0130")]
public class WhiteboardBehaviorOptions
{
    /// <summary>
    /// The maximum number of messages to keep on the whiteboard.
    /// </summary>
    /// <value>
    /// Defaults to 10 if not specified.
    /// </value>
    public int? MaxWhiteboardMessages { get; set; }

    /// <summary>
    /// When providing the messages that are currently on the whiteboard, this string is prefixed
    /// to those memories, in order to provide some context to the model.
    /// </summary>
    /// <value>
    /// Defaults to &quot;## Whiteboard\nThe following list of messages are currently on the whiteboard:&quot;
    /// </value>
    public string? ContextPrompt { get; init; }

    /// <summary>
    /// This message is provided to the model when there are no messages on the whiteboard.
    /// </summary>
    /// <value>
    /// Defaults to &quot;## Whiteboard\nThe whiteboard is currently empty.&quot;
    /// </value>
    public string? WhiteboardEmptyPrompt { get; init; }
}
