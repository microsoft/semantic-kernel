// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Orchestration.Extensions;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

internal class CodeBlock : Block
{
    internal override BlockTypes Type => BlockTypes.Code;

    internal CodeBlock(string content, ILogger log) : base(log)
    {
        this.Content = content;
    }

#pragma warning disable CA2254 // error strings are used also internally, not just for logging
    // ReSharper disable TemplateIsNotCompileTimeConstantProblem
    internal override bool IsValid(out string error)
    {
        error = "";

        List<string> partsToValidate = this.Content.Split(' ', '\t', '\r', '\n')
            .Where(x => !string.IsNullOrEmpty(x.Trim()))
            .ToList();

        for (var index = 0; index < partsToValidate.Count; index++)
        {
            var part = partsToValidate[index];

            if (index == 0) // There is only a function name
            {
                if (VarBlock.HasVarPrefix(part))
                {
                    error = $"Variables cannot be used as function names [`{part}`]";

                    this.Log.LogError(error);
                    return false;
                }

                if (!Regex.IsMatch(part, "^[a-zA-Z0-9_.]*$"))
                {
                    error = $"The function name `{part}` contains invalid characters";
                    this.Log.LogError(error);
                    return false;
                }
            }
            else // The function has parameters
            {
                if (!VarBlock.HasVarPrefix(part))
                {
                    error = $"`{part}` is not a valid function parameter: parameters must be variables.";
                    this.Log.LogError(error);
                    return false;
                }

                if (part.Length < 2)
                {
                    error = $"`{part}` is not a valid variable.";
                    this.Log.LogError(error);
                    return false;
                }

                if (!VarBlock.IsValidVarName(part.Substring(1)))
                {
                    error = $"`{part}` variable name is not valid.";
                    this.Log.LogError(error);
                    return false;
                }
            }
        }

        this._validated = true;

        return true;
    }
    // ReSharper restore TemplateIsNotCompileTimeConstantProblem
#pragma warning restore CA2254

    internal override string Render(ContextVariables? variables)
    {
        throw new InvalidOperationException(
            "Code blocks rendering requires IReadOnlySkillCollection. Incorrect method call.");
    }

#pragma warning disable CA2254 // error strings are used also internally, not just for logging
    // ReSharper disable TemplateIsNotCompileTimeConstantProblem
    internal override async Task<string> RenderCodeAsync(SKContext context)
    {
        if (!this._validated && !this.IsValid(out var error))
        {
            throw new TemplateException(TemplateException.ErrorCodes.SyntaxError, error);
        }

        this.Log.LogTrace("Rendering code: `{0}`", this.Content);

        List<string> parts = this.Content.Split(' ', '\t', '\r', '\n')
            .Where(x => !string.IsNullOrEmpty(x.Trim()))
            .ToList();

        var functionName = parts[0];
        context.ThrowIfSkillCollectionNotSet();
        if (!this.GetFunctionFromSkillCollection(context.Skills!, functionName, out ISKFunction? function))
        {
            var errorMsg = $"Function not found `{functionName}`";
            this.Log.LogError(errorMsg);
            throw new TemplateException(TemplateException.ErrorCodes.FunctionNotFound, errorMsg);
        }

        // ReSharper disable once NullCoalescingConditionIsAlwaysNotNullAccordingToAPIContract
        // Using $input by default, e.g. when the syntax is {{functionName}}

        // TODO: unit test, verify that all context variables are passed to Render()
        ContextVariables variablesClone = context.Variables.Clone();
        if (parts.Count > 1)
        {
            this.Log.LogTrace("Passing required variable: `{0}`", parts[1]);
            // If the code syntax is {{functionName $varName}} use $varName instead of $input
            string value = new VarBlock(parts[1], this.Log).Render(variablesClone);
            variablesClone.Update(value);
        }

        var result = await function.InvokeWithCustomInputAsync(
            variablesClone,
            context.Memory,
            context.Skills,
            this.Log,
            context.CancellationToken);

        if (result.ErrorOccurred)
        {
            var errorMsg = $"Function `{functionName}` execution failed. {result.LastException?.GetType().FullName}: {result.LastErrorDescription}";
            this.Log.LogError(errorMsg);
            throw new TemplateException(TemplateException.ErrorCodes.RuntimeError, errorMsg, result.LastException);
        }

        return result.Result;
    }
    // ReSharper restore TemplateIsNotCompileTimeConstantProblem
#pragma warning restore CA2254

    #region private ================================================================================

    private bool _validated;

    private bool GetFunctionFromSkillCollection(IReadOnlySkillCollection skills, string functionName,
        [NotNullWhen(true)] out ISKFunction? function)
    {
        // Search in the global space (only native functions there)
        if (skills.HasNativeFunction(functionName))
        {
            function = skills.GetNativeFunction(functionName);
            return true;
        }

        // If the function contains a skill name...
        if (functionName.Contains('.', StringComparison.InvariantCulture))
        {
            var functionNameParts = functionName.Split('.');
            if (functionNameParts.Length > 2)
            {
                this.Log.LogError("Invalid function name `{0}`", functionName);
                throw new ArgumentOutOfRangeException(
                    $"Invalid function name `{functionName}`. " +
                    "A Function name can contain only one `.` to separate skill name from function name.");
            }

            var skillName = functionNameParts[0];
            functionName = functionNameParts[1];

            if (skills.HasNativeFunction(skillName, functionName))
            {
                function = skills.GetNativeFunction(skillName, functionName);
                return true;
            }

            if (skills.HasSemanticFunction(skillName, functionName))
            {
                function = skills.GetSemanticFunction(skillName, functionName);
                return true;
            }
        }

        function = null;
        return false;
    }

    #endregion
}
