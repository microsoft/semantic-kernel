// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to prompt before rendering.
/// </summary>
[Experimental("SKEXP0001")]
[Obsolete("This class is deprecated in favor of PromptRenderContext class, which is used in IPromptRenderFilter interface.")]
public sealed class PromptRenderingContext : PromptFilterContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="PromptRenderingContext"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this filter is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    public PromptRenderingContext(KernelFunction function, KernelArguments arguments)
        : base(function, arguments, metadata: null)
    {
    }
}
