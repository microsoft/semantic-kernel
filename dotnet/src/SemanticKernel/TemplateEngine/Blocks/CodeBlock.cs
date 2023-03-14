// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Orchestration.Extensions;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

#pragma warning disable CA2254 // error strings are used also internally, not just for logging
// ReSharper disable TemplateIsNotCompileTimeConstantProblem
internal class CodeBlock : Block
{
    internal override BlockTypes Type => BlockTypes.Code;

    internal override bool? SynchronousRendering => false;

    internal CodeBlock(string? content, ILogger log)
        : this(new CodeTokenizer(log).Tokenize(content), content?.Trim(), log)
    {
    }

    internal CodeBlock(List<Block> tokens, string? content, ILogger log)
        : base(content?.Trim(), log)
    {
        this._tokens = tokens;
    }

    internal override bool IsValid(out string error)
    {
        error = "";

        foreach (Block token in this._tokens)
        {
            if (!token.IsValid(out error))
            {
                this.Log.LogError(error);
                return false;
            }
        }

        if (this._tokens.Count > 1)
        {
            if (this._tokens[0].Type != BlockTypes.FunctionId)
            {
                error = $"Unexpected second token found: {this._tokens[1].Content}";
                this.Log.LogError(error);
                return false;
            }

            if (this._tokens[1].Type != BlockTypes.Value && this._tokens[1].Type != BlockTypes.Variable)
            {
                error = "Functions support only one parameter";
                this.Log.LogError(error);
                return false;
            }
        }

        if (this._tokens.Count > 2)
        {
            error = $"Unexpected second token found: {this._tokens[1].Content}";
            this.Log.LogError(error);
            return false;
        }

        this._validated = true;

        return true;
    }

    internal override async Task<string> RenderCodeAsync(SKContext context)
    {
        if (!this._validated && !this.IsValid(out var error))
        {
            throw new TemplateException(TemplateException.ErrorCodes.SyntaxError, error);
        }

        this.Log.LogTrace("Rendering code: `{0}`", this.Content);

        switch (this._tokens[0].Type)
        {
            case BlockTypes.Value:
            case BlockTypes.Variable:
                return this._tokens[0].Render(context.Variables);

            case BlockTypes.FunctionId:
                return await this.RenderFunctionCallAsync((FunctionIdBlock)this._tokens[0], context);
        }

        throw new TemplateException(TemplateException.ErrorCodes.UnexpectedBlockType,
            $"Unexpected first token type: {this._tokens[0].Type:G}");
    }

    #region private ================================================================================

    private bool _validated;
    private readonly List<Block> _tokens;

    private async Task<string> RenderFunctionCallAsync(FunctionIdBlock fBlock, SKContext context)
    {
        context.ThrowIfSkillCollectionNotSet();
        if (!this.GetFunctionFromSkillCollection(context.Skills!, fBlock, out ISKFunction? function))
        {
            var errorMsg = $"Function `{fBlock.Content}` not found";
            this.Log.LogError(errorMsg);
            throw new TemplateException(TemplateException.ErrorCodes.FunctionNotFound, errorMsg);
        }

        ContextVariables variablesClone = context.Variables.Clone();

        // If the code syntax is {{functionName $varName}} use $varName instead of $input
        // If the code syntax is {{functionName 'value'}} use "value" instead of $input
        if (this._tokens.Count > 1)
        {
            // TODO: PII
            this.Log.LogTrace("Passing variable/value: `{0}`", this._tokens[1].Content);
            string input = this._tokens[1].Render(variablesClone);
            variablesClone.Update(input);
        }

        SKContext result = await function.InvokeWithCustomInputAsync(
            variablesClone,
            context.Memory,
            context.Skills,
            this.Log,
            context.CancellationToken);

        if (result.ErrorOccurred)
        {
            var errorMsg = $"Function `{fBlock.Content}` execution failed. {result.LastException?.GetType().FullName}: {result.LastErrorDescription}";
            this.Log.LogError(errorMsg);
            throw new TemplateException(TemplateException.ErrorCodes.RuntimeError, errorMsg, result.LastException);
        }

        return result.Result;
    }

    private bool GetFunctionFromSkillCollection(
        IReadOnlySkillCollection skills,
        FunctionIdBlock fBlock,
        [NotNullWhen(true)] out ISKFunction? function)
    {
        // Function in the global skill
        if (string.IsNullOrEmpty(fBlock.SkillName) && skills.HasFunction(fBlock.FunctionName))
        {
            function = skills.GetFunction(fBlock.FunctionName);
            return true;
        }

        // Function within a specific skill
        if (!string.IsNullOrEmpty(fBlock.SkillName) && skills.HasFunction(fBlock.SkillName, fBlock.FunctionName))
        {
            function = skills.GetFunction(fBlock.SkillName, fBlock.FunctionName);
            return true;
        }

        function = null;
        return false;
    }

    #endregion
}
// ReSharper restore TemplateIsNotCompileTimeConstantProblem
#pragma warning restore CA2254
