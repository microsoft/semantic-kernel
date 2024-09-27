// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Class that holds extension methods for objects implementing ISKFunction.
/// </summary>
public static class SKFunctionExtensions
{
    /// <summary>
    /// Execute a function with a custom set of context variables.
    /// Use case: template engine: semantic function with custom input variable.
    /// </summary>
    /// <param name="function">Function to execute</param>
    /// <param name="input">Custom function input</param>
    /// <param name="memory">Semantic memory</param>
    /// <param name="skills">Available skills</param>
    /// <param name="log">App logger</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The temporary context</returns>
    public static async Task<SKContext> InvokeWithCustomInputAsync(this ISKFunction function,
        ContextVariables input,
        // ISemanticTextMemory memory,
        // IReadOnlySkillCollection? skills,
        ILogger log
        // CancellationToken cancellationToken = default
    )
    {
        // var tmpContext = new SKContext(input, memory, skills, log, cancellationToken);
        var tmpContext = new SKContext(input);
        try
        return function.InvokeAsync(input, settings: null, memory: null, logger: null, cancellationToken: cancellationToken);
    }

    /// <summary>
    /// Execute a function allowing to pass the main input separately from the rest of the context.
    /// Note: if the context contains an INPUT key/value, that value is ignored, logging a warning.
    /// </summary>
    /// <param name="function">Function to execute</param>
    /// <param name="input">Main input string</param>
    /// <param name="context">Execution context, including variables other than input</param>
    /// <param name="mutableContext">Whether the function can modify the context variables, True by default</param>
    /// <param name="textCompletionService">Text completion service</param>
    /// <param name="settings">LLM completion settings (for semantic functions only)</param>
    /// <returns>The result of the function execution</returns>
    public static Task<SKContext> InvokeAsync(this ISKFunction function,
        string input,
        SKContext context,
        bool mutableContext = true,
        ITextCompletion? textCompletionService = null,
        CompleteRequestSettings? settings = null)
    {
        // Log a warning if the given input is overriding a different input in the context
        var inputInContext = context.Variables.Input;
        if (!string.IsNullOrEmpty(inputInContext) && !string.Equals(input, inputInContext, StringComparison.Ordinal))
        {
#pragma warning disable CA2016 // the token is passed in via the context
            await function.InvokeAsync(tmpContext).ConfigureAwait(false);
#pragma warning restore CA2016
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            log.LogError(ex, "Something went wrong when invoking function with custom input: {0}.{1}. Error: {2}", function.SkillName,
                function.Name, ex.Message);
            tmpContext.Fail(ex.Message, ex);
        }

        return tmpContext;
            return function.InvokeAsync(context, textCompletionService, settings);
        }

        // Create a copy of the context, to avoid editing the original set of variables
        SKContext contextClone = context.Clone();

        // Store the input in the context clone
        contextClone.Variables.Update(input);

        return function.InvokeAsync(contextClone, textCompletionService, settings);
    }
}
