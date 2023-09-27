// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Prompt.Blocks;

internal sealed class VarBlock : Block, ITextRendering
{
    internal override BlockTypes Type => BlockTypes.Variable;

    internal string Name { get; } = string.Empty;

    public VarBlock(string? content, ILoggerFactory? loggerFactory = null) : base(content?.Trim(), loggerFactory)
    {
        if (this.Content.Length < 2)
        {
            this.Logger.LogError("The variable name is empty");
            return;
        }

        this.Name = this.Content.Substring(1);
    }

#pragma warning disable CA2254 // error strings are used also internally, not just for logging
    // ReSharper disable TemplateIsNotCompileTimeConstantProblem
    public override bool IsValid(out string errorMsg)
    {
        errorMsg = string.Empty;

        if (string.IsNullOrEmpty(this.Content))
        {
            errorMsg = $"A variable must start with the symbol {Symbols.VarPrefix} and have a name";
            this.Logger.LogError(errorMsg);
            return false;
        }

        if (!IsVarPrefix(this.Content[0]))
        {
            errorMsg = $"A variable must start with the symbol {Symbols.VarPrefix}";
            this.Logger.LogError(errorMsg);
            return false;
        }

        if (this.Content.Length < 2)
        {
            errorMsg = "The variable name is empty";
            this.Logger.LogError(errorMsg);
            return false;
        }

        if (!s_validNameRegex.IsMatch(this.Name))
        {
            errorMsg = $"The variable name '{this.Name}' contains invalid characters. " +
                       "Only alphanumeric chars and underscore are allowed.";
            this.Logger.LogError(errorMsg);
            return false;
        }

        return true;
    }
#pragma warning restore CA2254

    public string Render(ContextVariables? variables)
    {
        if (variables == null) { return string.Empty; }

        if (string.IsNullOrEmpty(this.Name))
        {
            const string ErrMsg = "Variable rendering failed, the variable name is empty";
            this.Logger.LogError(ErrMsg);
            throw new SKException(ErrMsg);
        }

        if (variables.TryGetValue(this.Name, out string? value))
        {
            return value;
        }

        this.Logger.LogWarning("Variable `{0}{1}` not found", Symbols.VarPrefix, this.Name);

        return string.Empty;
    }

    private static readonly Regex s_validNameRegex = new("^[a-zA-Z0-9_]*$");
}
