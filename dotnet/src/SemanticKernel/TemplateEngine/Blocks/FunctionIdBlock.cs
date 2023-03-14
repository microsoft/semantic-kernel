// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal class FunctionIdBlock : Block
{
    internal override BlockTypes Type => BlockTypes.FunctionId;

    internal override bool? SynchronousRendering => true;

    internal string SkillName { get; } = string.Empty;

    internal string FunctionName { get; } = string.Empty;

    internal FunctionIdBlock(string? text, ILogger? log = null)
        : base(text?.Trim(), log)
    {
        var functionNameParts = this.Content.Split('.');
        if (functionNameParts.Length > 2)
        {
            this.Log.LogError("Invalid function name `{0}`", this.Content);
            throw new TemplateException(TemplateException.ErrorCodes.SyntaxError,
                "A function name can contain at most one dot separating the skill name from the function name");
        }

        if (functionNameParts.Length == 2)
        {
            this.SkillName = functionNameParts[0];
            this.FunctionName = functionNameParts[1];
            return;
        }

        this.FunctionName = this.Content;
    }

    internal override bool IsValid(out string error)
    {
        if (!Regex.IsMatch(this.Content, "^[a-zA-Z0-9_.]*$"))
        {
            error = "The function identifier is empty";
            return false;
        }

        if (HasMoreThanOneDot(this.Content))
        {
            error = "The function identifier can contain max one '.' char separating skill name from function name";
            return false;
        }

        error = "";
        return true;
    }

    internal override string Render(ContextVariables? variables)
    {
        return this.Content;
    }

    private static bool HasMoreThanOneDot(string? value)
    {
        if (value == null || value.Length < 2) { return false; }

        int count = 0;
        return value.Any(t => t == '.' && ++count > 1);
    }
}
