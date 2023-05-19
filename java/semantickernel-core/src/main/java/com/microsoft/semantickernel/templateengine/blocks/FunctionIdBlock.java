// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.semantickernel.orchestration.ReadOnlyContextVariables;

import javax.annotation.Nullable;

public class FunctionIdBlock extends Block implements TextRendering {
    public FunctionIdBlock(String content) {
        super(content, BlockTypes.FunctionId);
    }

    @Override
    public boolean isValid() {
        return false;
    }

    @Override
    @Nullable
    public String render(ReadOnlyContextVariables variables) {
        return null;
    }
    /*
    internal override BlockTypes Type => BlockTypes.FunctionId;

    internal string SkillName { get; } = string.Empty;

    internal string FunctionName { get; } = string.Empty;

    public FunctionIdBlock(string? text, ILogger? log = null)
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

    public override bool IsValid(out string errorMsg)
    {
        if (!Regex.IsMatch(this.Content, "^[a-zA-Z0-9_.]*$"))
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

     */
}
