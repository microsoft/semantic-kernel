// Copyright (c) Microsoft. All rights reserved.

using System.Threading;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to prompt rendering.
/// </summary>
public sealed class PromptRenderContext
{
    private string? _renderedPrompt;

    /// <summary>
    /// Initializes a new instance of the <see cref="PromptRenderContext"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="function">The <see cref="KernelFunction"/> with which this filter is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    internal PromptRenderContext(Kernel kernel, KernelFunction function, KernelArguments arguments)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(function);
        Verify.NotNull(arguments);

        this.Kernel = kernel;
        this.Function = function;
        this.Arguments = arguments;
    }

    /// <summary>
    /// The <see cref="System.Threading.CancellationToken"/> to monitor for cancellation requests.
    /// The default is <see cref="CancellationToken.None"/>.
    /// </summary>
    public CancellationToken CancellationToken { get; init; }

    /// <summary>
    /// Boolean flag which indicates whether a filter is invoked within streaming or non-streaming mode.
    /// </summary>
    public bool IsStreaming { get; init; }

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel Kernel { get; }

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this filter is associated.
    /// </summary>
    public KernelFunction Function { get; }

    /// <summary>
    /// Gets the arguments associated with the operation.
    /// </summary>
    public KernelArguments Arguments { get; }

    /// <summary>
    /// The execution settings associated with the operation.
    /// </summary>
    public PromptExecutionSettings? ExecutionSettings { get; init; }

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

    /// <summary>
    /// Gets or sets the result of the function's invocation.
    /// Setting <see cref="Result"/> to a non-<c>null</c> value will skip function invocation and return the result.
    /// </summary>
    public FunctionResult? Result { get; set; }
}
