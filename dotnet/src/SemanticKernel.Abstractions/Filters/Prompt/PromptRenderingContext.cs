// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to prompt rendering.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class PromptRenderingContext
{
    private string? _renderedPrompt;

    /// <summary>
    /// Initializes a new instance of the <see cref="PromptRenderingContext"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this filter is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    internal PromptRenderingContext(KernelFunction function, KernelArguments arguments)
    {
        Verify.NotNull(function);
        Verify.NotNull(arguments);

        this.Function = function;
        this.Arguments = arguments;
    }

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this filter is associated.
    /// </summary>
    public KernelFunction Function { get; }

    /// <summary>
    /// Gets the arguments associated with the operation.
    /// </summary>
    public KernelArguments Arguments { get; }

    /// <summary>
    /// Gets or sets the rendered prompt.
    /// </summary>
    /// <remarks>
    /// The filter may view the rendered prompt and change it, if desired.
    /// If there are multiple filters registered, subsequent filters may
    /// overwrite a value set by a previous filter. The final result is what will
    /// be the prompt used by the system.
    /// </remarks>
    public string? RenderedPrompt
    {
        get => this._renderedPrompt;
        set
        {
            Verify.NotNullOrWhiteSpace(value);
            this._renderedPrompt = value;
        }
    }
}
