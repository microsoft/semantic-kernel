// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments available to the Kernel.PromptRendered event.
/// </summary>
public class PromptRenderedEventArgs : KernelCancelEventArgs
{
    /// <summary>
    /// Initializes a new instance of the <see cref="PromptRenderedEventArgs"/> class.
    /// </summary>
    /// <param name="function">Kernel function</param>
    /// <param name="arguments">Kernel function arguments</param>
    /// <param name="renderedPrompt">Rendered prompt</param>
    public PromptRenderedEventArgs(KernelFunction function, KernelFunctionArguments arguments, string renderedPrompt) : base(function, arguments)
    {
        this.RenderedPrompt = renderedPrompt;
    }

    /// <summary>
    /// Rendered prompt.
    /// </summary>
    public string RenderedPrompt { get; set; }
}
