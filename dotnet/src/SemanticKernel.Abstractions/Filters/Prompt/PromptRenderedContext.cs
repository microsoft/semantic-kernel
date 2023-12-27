// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

public class PromptRenderedContext : PromptFilterContext
{
    private string _renderedPrompt;

    public PromptRenderedContext(KernelFunction function, KernelArguments arguments, string renderedPrompt)
        : base(function, arguments, metadata: null)
    {
        Verify.NotNull(renderedPrompt);
        this._renderedPrompt = renderedPrompt;
    }

    public bool Cancel { get; set; }

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
