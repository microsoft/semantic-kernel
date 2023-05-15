// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.templateengine.TemplateException;

public class VarBlock extends Block implements TextRendering {

    private final String name;

    public VarBlock(String content) {
        super(content, BlockTypes.Variable);

        this.name = content.substring(1);
    }

    @Override
    public boolean isValid() {
        return true;
    }

    @Override
    public String render(ContextVariables variables) {
        if (variables == null) {
            return "";
        }

        if (name == null || name.isEmpty()) {
            // TODO
            // const string errMsg = "Variable rendering failed, the variable name is empty";
            // this.Log.LogError(errMsg);
            // throw new TemplateException(TemplateException.ErrorCodes.SyntaxError, errMsg);
            throw new TemplateException();
        }

        String value = variables.asMap().get(name);

        if (value == null) {
            // TODO
            // this.Log.LogWarning("Variable `{0}{1}` not found", Symbols.VarPrefix, this.Name);
        }

        return value != null ? value : "";
    }
    /*
        internal override BlockTypes Type => BlockTypes.Variable;

        internal string Name { get; } = string.Empty;

        public VarBlock(string? content, ILogger? log = null) : base(content?.Trim(), log)
        {
            if (this.Content.Length < 2)
            {
                this.Log.LogError("The variable name is empty");
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
                this.Log.LogError(errorMsg);
                return false;
            }

            if (this.Content[0] != Symbols.VarPrefix)
            {
                errorMsg = $"A variable must start with the symbol {Symbols.VarPrefix}";
                this.Log.LogError(errorMsg);
                return false;
            }

            if (this.Content.Length < 2)
            {
                errorMsg = "The variable name is empty";
                this.Log.LogError(errorMsg);
                return false;
            }

            if (!Regex.IsMatch(this.Name, "^[a-zA-Z0-9_]*$"))
            {
                errorMsg = $"The variable name '{this.Name}' contains invalid characters. " +
                           "Only alphanumeric chars and underscore are allowed.";
                this.Log.LogError(errorMsg);
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
                const string errMsg = "Variable rendering failed, the variable name is empty";
                this.Log.LogError(errMsg);
                throw new TemplateException(TemplateException.ErrorCodes.SyntaxError, errMsg);
            }

            var exists = variables.Get(this.Name, out string value);
            if (!exists) { this.Log.LogWarning("Variable `{0}{1}` not found", Symbols.VarPrefix, this.Name); }

            return exists ? value : string.Empty;
        }

         */
}
