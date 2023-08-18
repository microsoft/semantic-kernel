// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal sealed class NamedArgBlock : Block, ITextRendering
{
    internal static char Separator = '=';

    internal override BlockTypes Type => BlockTypes.NamedArg;

    internal string Name { get; } = string.Empty;

    internal string Value { get; } = string.Empty;

    public NamedArgBlock(string? text, ILogger? logger = null)
        : base(NamedArgBlock.TrimWhitespace(text), logger)
    {
        var argParts = NamedArgBlock.GetTrimmedParts(text);
        if (argParts.Length == 2)
        {
            // TODO validate each part (can't have = sign for instance)
            this.Name = argParts[0];
            this.Value = argParts[1];
            return;
        }

        this.Logger.LogError("Invalid named argument `{0}`", this.Content);
        throw new TemplateException(TemplateException.ErrorCodes.SyntaxError,
            $"A function named argument must contain a name and value separated by a '{NamedArgBlock.Separator}'");
    }

    // TODO delete this comment once you confirm this Render method
    // doesn't matter too much
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

        if (string.IsNullOrEmpty(this.Value))
        {
            errorMsg = "A name argument must have a value";
            this.Logger.LogError(errorMsg);
            return false;
        }

        // Argument names share the same validation as variables
        var tempVar = new VarBlock($"${this.Name}");
        var isNameValid = tempVar.IsValid(out errorMsg);

        // Argument values share the same validation as values
        var tempVal = new ValBlock(this.Value);
        tempVal.IsValid(out errorMsg);
        var isValueValid = tempVal.IsValid(out errorMsg);

        return isNameValid && isValueValid;
    }
#pragma warning restore CA2254

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
                return $"{trimmedParts[0]}{NamedArgBlock.Separator}{trimmedParts[1]}";
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

        string[] parts = text.Split(new char[] { NamedArgBlock.Separator }, 2);
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
}
