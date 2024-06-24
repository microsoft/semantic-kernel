// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides a <see cref="CancelKernelEventArgs"/> used in events raised just after a prompt has been rendered.
/// </summary>
[Obsolete("Events are deprecated in favor of filters. Example in dotnet/samples/KernelSyntaxExamples/Getting_Started/Step7_Observability.cs of Semantic Kernel repository.")]
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
        this.RenderedPrompt = renderedPrompt;
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
        [MemberNotNull(nameof(_renderedPrompt))]
        set
        {
            Verify.NotNullOrWhiteSpace(value);
            this._renderedPrompt = value;
        }
    }
}
