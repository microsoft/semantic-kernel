// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal sealed class TextBlock : Block, ITextRendering
{
    internal override BlockTypes Type => BlockTypes.Text;

    public TextBlock(string? text, ILoggerFactory? loggerFactory = null)
        : base(text, loggerFactory)
    {
    }

    public TextBlock(string text, int startIndex, int stopIndex, ILoggerFactory? loggerFactory)
        : base(text.Substring(startIndex, stopIndex - startIndex), loggerFactory)
    {
    }

    public override bool IsValid(out string errorMsg)
    {
        errorMsg = "";
        return true;
    }

    /// <inheritdoc/>
    public string Render(IDictionary<string, string>? arguments)
    {
        return this.Content;
    }
}
