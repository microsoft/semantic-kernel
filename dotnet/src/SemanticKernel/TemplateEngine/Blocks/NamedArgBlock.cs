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
        if (valueIsValidValBlock && this._valBlock != null)
        {
            return this._valBlock.Render(variables);
        }

        var valueIsValidVarBlock = this._argValueAsVarBlock != null && this._argValueAsVarBlock.IsValid(out var errorMessage2);
        if (valueIsValidVarBlock && this._argValueAsVarBlock != null)
        {
            return this._argValueAsVarBlock.Render(variables);
        }

        return string.Empty;
    }

    public NamedArgBlock(string? text, ILoggerFactory? logger = null)
        : base(text?.Trim(), logger)
    {
        var argParts = this.Content.Split(Symbols.NamedArgBlockSeparator);
        if (argParts.Length > 2)
        {
            this.Logger.LogError("Invalid named argument `{NamedArg}`.", this.Content);
            throw new SKException($"Invalid named argument `{this.Content}`. A named argument can contain at most one equals sign separating the arg name from the arg value.");
        }

        if (argParts.Length == 2)
        {
            this.Name = argParts[0];
            this._argNameAsVarBlock = new VarBlock($"{Symbols.VarPrefix}{argParts[0]}");
            var secondPart = argParts[1];
            if (secondPart[0] == Symbols.VarPrefix)
            {
                this._argValueAsVarBlock = new VarBlock(secondPart);
            }
            else
            {
                this._valBlock = new ValBlock(argParts[1]);
            }

            return;
        }

        this.Logger.LogError("Invalid named argument `{0}`", this.Content);
        throw new SKException($"A function named argument must contain a name and value separated by a '{Symbols.NamedArgBlockSeparator}'");
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

    #endregion
}
