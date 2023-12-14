// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides an <see cref="EventArgs"/> for cancelable operations related
/// to <see cref="Kernel"/>-based operations.
/// </summary>
[Experimental("SKEXP0003")]
public abstract class CancelKernelEventArgs : KernelEventArgs
{
    /// <summary>
    /// Initializes a new instance of the <see cref="CancelKernelEventArgs"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this event is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    /// <param name="metadata">A dictionary of metadata associated with the operation.</param>
    internal CancelKernelEventArgs(KernelFunction function, KernelArguments arguments, IDictionary<string, object?>? metadata = null) :
        base(function, arguments, metadata)
    {
    }

    /// <summary>
    /// Gets or sets a value indicating whether the operation associated with
    /// the event should be canceled.
    /// </summary>
    /// <remarks>
    /// A cancelable event is raised by the system when it is about to perform an action
    /// that can be canceled, such as invoking a <see cref="KernelFunction"/>. The event
    /// handler may set <see cref="Cancel"/> to true to indicate that the operation should
    /// be canceled. If there are multiple event handlers registered, subsequent handlers
    /// may see and change a value set by a previous handler. The final result is what will
    /// be considered by the component raising the event.
    /// </remarks>
    public bool Cancel { get; set; }
}
