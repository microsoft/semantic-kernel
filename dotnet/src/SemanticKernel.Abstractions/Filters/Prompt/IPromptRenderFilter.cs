// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

#pragma warning disable CA1716 // Identifiers should not match keywords (Func<PromptRenderContext, Task> next)

/// <summary>
/// Interface for filtering actions during prompt rendering.
/// </summary>
public interface IPromptRenderFilter
{
    /// <summary>
    /// Method which is called asynchronously before prompt rendering.
    /// </summary>
    /// <param name="context">Instance of <see cref="PromptRenderContext"/> with prompt rendering details.</param>
    /// <param name="next">Delegate to the next filter in pipeline or prompt rendering operation itself. If it's not invoked, next filter or prompt rendering won't be invoked.</param>
    Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next);
}
