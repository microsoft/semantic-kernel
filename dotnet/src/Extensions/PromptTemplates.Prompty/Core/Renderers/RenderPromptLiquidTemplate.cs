// Copyright (c) Microsoft. All rights reserved.

using Scriban;

namespace Microsoft.SemanticKernel.Experimental.Prompty.Core;

internal class RenderPromptLiquidTemplate
{
    private readonly Prompty _prompty;

    // create private invokerfactory and init it
    public RenderPromptLiquidTemplate(Prompty prompty)
    {
        this._prompty = prompty;
    }

    public void RenderTemplate()
    {
        var template = Template.ParseLiquid(this._prompty.Prompt);
        this._prompty.Prompt = template.Render(this._prompty.Inputs);
    }
}
