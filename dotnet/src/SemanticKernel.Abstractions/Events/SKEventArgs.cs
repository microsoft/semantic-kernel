// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Base arguments for events.
/// </summary>
public abstract class SKEventArgs : EventArgs
{
    /// <summary>
    /// Initializes a new instance of the <see cref="SKEventArgs"/> class.
    /// </summary>
    /// <param name="metadata">Function metadata</param>
    /// <param name="context">Context related to the event</param>
    internal SKEventArgs(SKFunctionMetadata metadata, SKContext context)
    {
        Verify.NotNull(context);
        Verify.NotNull(metadata);

        this.FunctionMetadata = metadata;
        this.SKContext = context;
        this.Metadata = new();
    }

    /// <summary>
    /// Function metadata
    /// </summary>
    public SKFunctionMetadata FunctionMetadata { get; }

    /// <summary>
    /// Context related to the event.
    /// </summary>
    public SKContext SKContext { get; }

    /// <summary>
    /// Metadata for storing additional information about function execution result.
    /// </summary>
    public Dictionary<string, object> Metadata { get; protected set; }
}
