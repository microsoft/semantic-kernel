// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal sealed class NamedArgBlock : Block, ITextRendering
{
    internal override BlockTypes Type => BlockTypes.NamedArg;

    internal string Name { get; } = string.Empty;

    public string GetValue(ContextVariables? variables)
    {
        var valueIsValidValBlock = this._valBlock != null && this._valBlock.IsValid(out var errorMessage);
        if (valueIsValidValBlock)
        {
            return this._valBlock!.Render(variables);
        }

        var valueIsValidVarBlock = this._argValueAsVarBlock != null && this._argValueAsVarBlock.IsValid(out var errorMessage2);
        if (valueIsValidVarBlock)
        {
            return this._argValueAsVarBlock!.Render(variables);
        }

        return string.Empty;
    }

    public NamedArgBlock(string? text, ILoggerFactory? logger = null)
        : base(NamedArgBlock.TrimWhitespace(text), logger)
    {
        var argParts = this.Content.Split(Symbols.NamedArgBlockSeparator);
        if (argParts.Length > 2)
        {
            this.Logger.LogError("Invalid named argument `{0}`.", this.Content);
            throw new SKException($"Invalid named argument `{this.Content}`. A named argument can contain at most one equals sign separating the arg name from the arg value.");
        }

        if (argParts.Length == 2)
        {
            var trimmedArgParts = NamedArgBlock.GetTrimmedParts(text);
            this.Name = trimmedArgParts[0];
            this._argNameAsVarBlock = new VarBlock($"{Symbols.VarPrefix}{trimmedArgParts[0]}");
            var secondPart = trimmedArgParts[1];
            if (secondPart.Length == 0)
            {
                this.Logger.LogError("Invalid named argument `{0}`", this.Content);
                throw new SKException($"A function named argument must contain a quoted value or variable after the '{Symbols.NamedArgBlockSeparator}' character.");
            }
            else if (secondPart[0] == Symbols.VarPrefix)
            {
                this._argValueAsVarBlock = new VarBlock(secondPart);
            }
            else
            {
                this._valBlock = new ValBlock(trimmedArgParts[1]);
            }

            return;
        }

        this.Logger.LogError("Invalid named argument `{0}`", this.Content);
        throw new SKException($"A function named argument must contain a name and value separated by a '{Symbols.NamedArgBlockSeparator}' character.");
    }

    public string Render(ContextVariables? variables)
    {
        return this.Content;
    }

#pragma warning disable CA2254 // error strings are used also internally, not just for logging
    public override bool IsValid(out string errorMsg)
    {
        errorMsg = string.Empty;
        if (string.IsNullOrEmpty(this.Name))
        {
            errorMsg = "A named argument must have a name";
            this.Logger.LogError(errorMsg);
            return false;
        }

        var isValueValid = true;
        if (this._valBlock != null)
        {
            isValueValid = this._valBlock.IsValid(out errorMsg);
        }
        else if (this._argValueAsVarBlock != null)
        {
            isValueValid = this._argValueAsVarBlock.IsValid(out errorMsg);
        }
        else
        {
            errorMsg = "A name argument must have a value";
            this.Logger.LogError(errorMsg);
            return false;
        }

        // Argument names share the same validation as variables
        var isNameValid = this._argNameAsVarBlock.IsValid(out errorMsg);

        return isNameValid && isValueValid;
    }
#pragma warning restore CA2254

    #region private ================================================================================

    private readonly VarBlock _argNameAsVarBlock;
    private readonly ValBlock? _valBlock;
    private readonly VarBlock? _argValueAsVarBlock;

    private static string? TrimWhitespace(string? text)
    {
        if (text == null)
        {
            return text;
        }

        string[] trimmedParts = NamedArgBlock.GetTrimmedParts(text);
        switch (trimmedParts?.Length)
        {
            case (2):
                return $"{trimmedParts[0]}{Symbols.NamedArgBlockSeparator}{trimmedParts[1]}";
            case (1):
                return trimmedParts[0];
            default:
                return null;
        }
    }

    private static string[] GetTrimmedParts(string? text)
    {
        if (text == null)
        {
            return System.Array.Empty<string>();
        }

        string[] parts = text.Split(new char[] { Symbols.NamedArgBlockSeparator }, 2);
        string[] result = new string[parts.Length];
        if (parts.Length > 0)
        {
            result[0] = parts[0].Trim();
        }

        if (parts.Length > 1)
        {
            result[1] = parts[1].Trim();
        }

        return result;
    }

    #endregion
}
