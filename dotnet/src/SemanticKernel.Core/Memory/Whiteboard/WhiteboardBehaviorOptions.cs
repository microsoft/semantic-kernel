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
}
