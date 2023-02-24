// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

// ReSharper disable TemplateIsNotCompileTimeConstantProblem

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal class VarBlock : Block
{
    private const char Prefix = '$';

    internal override BlockTypes Type => BlockTypes.Variable;

    internal string Name => this.VarName();

    internal VarBlock(string content, ILogger? log = null) : base(log)
    {
        this.Content = content;
    }

#pragma warning disable CA2254 // error strings are used also internally, not just for logging
    internal override bool IsValid(out string error)
    {
        error = string.Empty;

        if (this.Content[0] != Prefix)
        {
            error = $"A variable must start with the symbol {Prefix}";
            this.Log.LogError(error);
            return false;
        }

        if (this.Content.Length < 2)
        {
            error = "The variable name is empty";
            this.Log.LogError(error);
            return false;
        }

        var varName = this.VarName();
        if (!Regex.IsMatch(varName, "^[a-zA-Z0-9_]*$"))
        {
            error = $"The variable name '{varName}' contains invalid characters. " +
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

        var name = this.VarName();
        if (!string.IsNullOrEmpty(name))
        {
            var exists = variables.Get(name, out string value);
            if (!exists) { this.Log.LogWarning("Variable `{0}{1}` not found", Prefix, name); }

            return exists ? value : "";
        }

        this.Log.LogError("Variable rendering failed, the variable name is empty");
        throw new TemplateException(
            TemplateException.ErrorCodes.SyntaxError, "Variable rendering failed, the variable name is empty.");
    }

    internal static bool HasVarPrefix(string text)
    {
        return !string.IsNullOrEmpty(text) && text.Length > 0 && text[0] == Prefix;
    }

    internal static bool IsValidVarName(string text)
    {
        return Regex.IsMatch(text, "^[a-zA-Z0-9_]*$");
    }

    private string VarName()
    {
        return this.Content.Length < 2 ? "" : this.Content[1..];
    }
}
