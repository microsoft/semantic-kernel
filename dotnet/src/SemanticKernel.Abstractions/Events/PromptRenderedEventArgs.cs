// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides a <see cref="CancelKernelEventArgs"/> used in events raised just after a prompt has been rendered.
/// </summary>
[Experimental("SKEXP0004")]
public sealed class PromptRenderedEventArgs : CancelKernelEventArgs
{
    private string _renderedPrompt;

    /// <summary>
    /// Initializes a new instance of the <see cref="PromptRenderedEventArgs"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this event is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    /// <param name="renderedPrompt">The prompt that was rendered by the associated operation.</param>
    public PromptRenderedEventArgs(KernelFunction function, KernelArguments arguments, string renderedPrompt) :
        base(function, arguments, metadata: null)
    {
        Verify.NotNull(renderedPrompt);
        this._renderedPrompt = renderedPrompt;
    }

    /// <summary>Gets or sets the rendered prompt.</summary>
    /// <remarks>
    /// An event handler may view the rendered prompt and change it, if desired.
    /// If there are multiple event handlers registered, subsequent handlers may
    /// overwrite a value set by a previous handler. The final result is what will
    /// be the prompt used by the system.
    /// </remarks>
    public string RenderedPrompt
    {
        get => this._renderedPrompt;
        set
        {
            Verify.NotNull(value);
            this._renderedPrompt = value;
        }
    }
}
