// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal sealed class TextBlock : Block, ITextRendering
{
    internal override BlockTypes Type => BlockTypes.Text;

    public TextBlock(string? text, ILogger? log = null)
        : base(text, log)
    {
    }

    public TextBlock(string text, int startIndex, int stopIndex, ILogger log)
        : base(text.Substring(startIndex, stopIndex - startIndex), log)
    {
    }

    public override bool IsValid(out string errorMsg)
    {
        errorMsg = "";
        return true;
    }

    public string Render(ContextVariables? variables)
    {
        return this.Content;
    }
}
