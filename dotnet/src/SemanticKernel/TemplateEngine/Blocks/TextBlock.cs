// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal class TextBlock : Block
{
    internal override BlockTypes Type => BlockTypes.Text;

    internal TextBlock(string content, ILogger? log = null)
        : base(log)
    {
        this.Content = content;
    }

    internal TextBlock(string text, int startIndex, int stopIndex, ILogger log)
        : base(log)
    {
        this.Content = text.Substring(startIndex, stopIndex - startIndex);
    }

    internal override bool IsValid(out string error)
    {
        error = "";
        return true;
    }

    internal override string Render(ContextVariables? variables)
    {
        return this.Content;
    }
}
