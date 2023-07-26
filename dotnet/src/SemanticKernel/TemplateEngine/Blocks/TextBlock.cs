// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal sealed class TextBlock : Block, ITextRendering
{
    internal override BlockTypes Type => BlockTypes.Text;

    public TextBlock(string? text, ILogger? logger = null)
        : base(text, logger)
    {
    }

    public TextBlock(string text, int startIndex, int stopIndex, ILogger logger)
        : base(text.Substring(startIndex, stopIndex - startIndex), logger)
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
