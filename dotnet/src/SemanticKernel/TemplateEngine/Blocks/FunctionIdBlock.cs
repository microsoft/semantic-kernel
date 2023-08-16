// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal sealed class FunctionIdBlock : Block, ITextRendering
{
    internal override BlockTypes Type => BlockTypes.FunctionId;

    internal string SkillName { get; } = string.Empty;

    internal string FunctionName { get; } = string.Empty;

    public FunctionIdBlock(string? text, ILogger? logger = null)
        : base(text?.Trim(), logger)
    {
        var functionNameParts = this.Content.Split('.');
        if (functionNameParts.Length > 2)
        {
#pragma warning disable CA2254 // Template should be a static expression. The code should be refactored as part of the semantic/structural logging adoption in SK.
            var errorMessage = $"Invalid function name `{this.Content}`. A function name can contain at most one dot separating the skill name from the function name";
            this.Logger.LogError(errorMessage);
            throw new SKException(errorMessage);
#pragma warning restore CA2254 // Template should be a static expression. The code should be refactored as part of the semantic/structural logging adoption in SK.
        }

        if (functionNameParts.Length == 2)
        {
            this.SkillName = functionNameParts[0];
            this.FunctionName = functionNameParts[1];
            return;
        }

        this.FunctionName = this.Content;
    }

    public override bool IsValid(out string errorMsg)
    {
        if (!s_validContentRegex.IsMatch(this.Content))
        {
            errorMsg = "The function identifier is empty";
            return false;
        }

        if (HasMoreThanOneDot(this.Content))
        {
            errorMsg = "The function identifier can contain max one '.' char separating skill name from function name";
            return false;
        }

        errorMsg = "";
        return true;
    }

    public string Render(ContextVariables? variables)
    {
        return this.Content;
    }

    private static bool HasMoreThanOneDot(string? value)
    {
        if (value == null || value.Length < 2) { return false; }

        int count = 0;
        return value.Any(t => t == '.' && ++count > 1);
    }

    private static readonly Regex s_validContentRegex = new("^[a-zA-Z0-9_.]*$");
}
