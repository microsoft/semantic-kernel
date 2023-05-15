// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.semantickernel.orchestration.ContextVariables;

import reactor.util.annotation.Nullable;

public class ValBlock extends Block implements TextRendering {
    public ValBlock(String content) {
        super(content, BlockTypes.Value);
    }

    @Override
    public boolean isValid() {
        return false;
    }

    @Override
    @Nullable
    public String render(ContextVariables variables) {
        return null;
    }

    /*
        internal override BlockTypes Type => BlockTypes.Value;

        // Cache the first and last char
        private readonly char _first = '\0';
        private readonly char _last = '\0';

        // Content, excluding start/end quote chars
        private readonly string _value = string.Empty;

        /// <summary>
        /// Create an instance
        /// </summary>
        /// <param name="quotedValue">Block content, including the delimiting chars</param>
        /// <param name="log">Optional logger</param>
        public ValBlock(string? quotedValue, ILogger? log = null)
            : base(quotedValue?.Trim(), log)
        {
            if (this.Content.Length < 2)
            {
                this.Log.LogError("A value must have single quotes or double quotes on both sides");
                return;
            }

            this._first = this.Content[0];
            this._last = this.Content[this.Content.Length - 1];
            this._value = this.Content.Substring(1, this.Content.Length - 2);
        }

    #pragma warning disable CA2254 // error strings are used also internally, not just for logging
        // ReSharper disable TemplateIsNotCompileTimeConstantProblem
        public override bool IsValid(out string errorMsg)
        {
            errorMsg = string.Empty;

            // Content includes the quotes, so it must be at least 2 chars long
            if (this.Content.Length < 2)
            {
                errorMsg = "A value must have single quotes or double quotes on both sides";
                this.Log.LogError(errorMsg);
                return false;
            }

            // Check if delimiting chars are consistent
            if (this._first != this._last)
            {
                errorMsg = "A value must be defined using either single quotes or double quotes, not both";
                this.Log.LogError(errorMsg);
                return false;
            }

            return true;
        }
    #pragma warning restore CA2254

        public string Render(ContextVariables? variables)
        {
            return this._value;
        }

        public static bool HasValPrefix(string? text)
        {
            return !text.IsNullOrEmpty()
                   && text.Length > 0
                   && (text[0] is Symbols.DblQuote or Symbols.SglQuote);
        }*/
}
