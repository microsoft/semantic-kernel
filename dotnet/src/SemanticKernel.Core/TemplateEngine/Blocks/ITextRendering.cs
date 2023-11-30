// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

/// <summary>
/// Interface of static blocks that don't need async IO to be rendered.
/// </summary>
internal interface ITextRendering
{
    /// <summary>
    /// Render the block using only the given variables.
    /// </summary>
    /// <param name="arguments">Optional arguments used to render the block</param>
    /// <returns>Rendered content</returns>
    public string Render(IDictionary<string, string>? arguments);
}
