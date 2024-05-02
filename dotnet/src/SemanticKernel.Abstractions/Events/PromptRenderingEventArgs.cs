// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides a <see cref="KernelEventArgs"/> used in events raised just before a prompt is rendered.
/// </summary>
[Obsolete("Events are deprecated in favor of filters. Example in dotnet/samples/GettingStarted/Step7_Observability.cs of Semantic Kernel repository.")]
public sealed class PromptRenderingEventArgs : KernelEventArgs
{
    /// <summary>
    /// Initializes a new instance of the <see cref="PromptRenderingEventArgs"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this event is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    public PromptRenderingEventArgs(KernelFunction function, KernelArguments arguments) :
        base(function, arguments, metadata: null)
    {
    }
}
