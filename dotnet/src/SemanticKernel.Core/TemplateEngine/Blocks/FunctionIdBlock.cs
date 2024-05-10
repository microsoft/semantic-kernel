// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.TemplateEngine;

internal sealed partial class FunctionIdBlock : Block, ITextRendering
{
    internal override BlockTypes Type => BlockTypes.FunctionId;

    internal string PluginName { get; } = string.Empty;

    internal string FunctionName { get; } = string.Empty;

    public FunctionIdBlock(string? text, ILoggerFactory? loggerFactory = null)
        : base(text?.Trim(), loggerFactory)
    {
        var functionNameParts = this.Content.Split('.');
        if (functionNameParts.Length > 2)
        {
            this.Logger.LogError("Invalid function name `{FunctionName}`.", this.Content);
            throw new KernelException($"Invalid function name `{this.Content}`. A function name can contain at most one dot separating the plugin name from the function name");
        }

        if (functionNameParts.Length == 2)
        {
            this.PluginName = functionNameParts[0];
            this.FunctionName = functionNameParts[1];
            return;
        }

        this.FunctionName = this.Content;
    }

    public override bool IsValid(out string errorMsg)
    {
        if (!ValidContentRegex().IsMatch(this.Content))
        {
            errorMsg = "The function identifier is empty";
            return false;
        }

        if (HasMoreThanOneDot(this.Content))
        {
            errorMsg = "The function identifier can contain max one '.' char separating plugin name from function name";
            return false;
        }

        errorMsg = "";
        return true;
    }

    /// <inheritdoc/>
    public object? Render(KernelArguments? arguments)
    {
        return this.Content;
    }

    private static bool HasMoreThanOneDot(string? value)
    {
        if (value is null || value.Length < 2) { return false; }

        int count = 0;
        return value.Any(t => t == '.' && ++count > 1);
    }

#if NET
    [GeneratedRegex("^[a-zA-Z0-9_.]*$")]
    private static partial Regex ValidContentRegex();
#else
    private static Regex ValidContentRegex() => s_validContentRegex;
    private static readonly Regex s_validContentRegex = new("^[a-zA-Z0-9_.]*$");
#endif
}
