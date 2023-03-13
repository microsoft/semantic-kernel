// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal class VarBlock : Block
{
    internal override BlockTypes Type => BlockTypes.Variable;

    internal override bool? SynchronousRendering => true;

    internal string Name { get; } = string.Empty;

    internal VarBlock(string? content, ILogger? log = null) : base(content?.Trim(), log)
    {
        if (this.Content.Length < 2)
        {
            this.Log.LogError("The variable name is empty");
            return;
        }

        this.Name = this.Content[1..];
    }

#pragma warning disable CA2254 // error strings are used also internally, not just for logging
    // ReSharper disable TemplateIsNotCompileTimeConstantProblem
    internal override bool IsValid(out string error)
    {
        error = string.Empty;

        if (string.IsNullOrEmpty(this.Content))
        {
            error = $"A variable must start with the symbol {Symbols.VarPrefix} and have a name";
            this.Log.LogError(error);
            return false;
        }

        if (this.Content[0] != Symbols.VarPrefix)
        {
            error = $"A variable must start with the symbol {Symbols.VarPrefix}";
            this.Log.LogError(error);
            return false;
        }

        if (this.Content.Length < 2)
        {
            error = "The variable name is empty";
            this.Log.LogError(error);
            return false;
        }

        if (!Regex.IsMatch(this.Name, "^[a-zA-Z0-9_]*$"))
        {
            error = $"The variable name '{this.Name}' contains invalid characters. " +
                    "Only alphanumeric chars and underscore are allowed.";
            this.Log.LogError(error);
            return false;
        }

        return true;
    }
#pragma warning restore CA2254

    internal override string Render(ContextVariables? variables)
    {
        if (variables == null) { return string.Empty; }

        if (string.IsNullOrEmpty(this.Name))
        {
            const string errMsg = "Variable rendering failed, the variable name is empty";
            this.Log.LogError(errMsg);
            throw new TemplateException(TemplateException.ErrorCodes.SyntaxError, errMsg);
        }

        var exists = variables.Get(this.Name, out string value);
        if (!exists) { this.Log.LogWarning("Variable `{0}{1}` not found", Symbols.VarPrefix, this.Name); }

        return exists ? value : "";
    }
}
