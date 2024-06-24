// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Interface for filtering actions during prompt rendering.
/// </summary>
[Experimental("SKEXP0001")]
public interface IPromptFilter
{
    /// <summary>
    /// Method which is executed before prompt rendering.
    /// </summary>
    /// <param name="context">Data related to prompt before rendering.</param>
    void OnPromptRendering(PromptRenderingContext context);

    /// <summary>
    /// Method which is executed after prompt rendering.
    /// </summary>
    /// <param name="context">Data related to prompt after rendering.</param>
    void OnPromptRendered(PromptRenderedContext context);
}
