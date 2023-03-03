// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal class TextBlock : Block
{
    internal override BlockTypes Type => BlockTypes.Text;

    internal override bool? SynchronousRendering => true;

    internal TextBlock(string? text, ILogger? log = null)
        : base(text, log)
    {
    }

    internal TextBlock(string text, int startIndex, int stopIndex, ILogger log)
        : base(text.Substring(startIndex, stopIndex - startIndex), log)
    {
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
