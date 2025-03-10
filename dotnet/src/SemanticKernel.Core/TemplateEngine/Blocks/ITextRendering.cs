// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// Interface of static blocks that don't need async IO to be rendered.
/// </summary>
internal interface ITextRendering
{
    /// <summary>
    /// Render the block using only the given arguments.
    /// </summary>
    /// <param name="arguments">Optional arguments the block rendering</param>
    /// <returns>Rendered content</returns>
    object? Render(KernelArguments? arguments);
}
