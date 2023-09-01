// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;

namespace Microsoft.SemanticKernel.SkillDefinition;

#pragma warning disable format

/// <summary>
/// A Semantic Kernel "Semantic" prompt function.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
internal sealed class SemanticFunction : FunctionBase, ISKFunction, IDisposable
{
    /// <inheritdoc/>
    public override bool IsSemantic => true;

    /// <summary>
    /// Prompt template engine.
    /// </summary>
    public IPromptTemplate PromptTemplate { get; }

    /// <summary>
    /// Create a native function instance, given a semantic function configuration.
    /// </summary>
    /// <param name="skillName">Name of the skill to which the function to create belongs.</param>
    /// <param name="functionName">Name of the function to create.</param>
    /// <param name="functionConfig">Semantic function configuration.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>SK function instance.</returns>
    public static ISKFunction FromSemanticConfig(
        string skillName,
        string functionName,
        SemanticFunctionConfig functionConfig,
        ILoggerFactory? loggerFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(functionConfig);

        var func = new SemanticFunction(
            template: functionConfig.PromptTemplate,
            description: functionConfig.PromptTemplateConfig.Description,
            skillName: skillName,
            functionName: functionName,
            loggerFactory: loggerFactory
        );

        return func;
    }

    /// <inheritdoc/>
    public override async Task<SKContext> InvokeAsync(
        SKContext context,
        CompleteRequestSettings? settings = null,
        CancellationToken cancellationToken = default)
    {
        context.InternalVariables.TryGetValue(RenderedPromptKey, out string? renderedPrompt);
        if (renderedPrompt is null)
        {
            this.AddDefaultValues(context.Variables);
            renderedPrompt = await this.RenderPromptTemplateAsync(context, cancellationToken).ConfigureAwait(false);
        }

        return await this.RunPromptAsync(this._aiService?.Value, settings ?? this.RequestSettings, context, renderedPrompt, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills)
    {
        this._skillCollection = skills;
        return this;
    }

    /// <inheritdoc/>
    public override ISKFunction SetAIService(Func<ITextCompletion> serviceFactory)
    {
        Verify.NotNull(serviceFactory);
        this._aiService = new Lazy<ITextCompletion>(serviceFactory);
        return this;
    }

    /// <inheritdoc/>
    public override ISKFunction SetAIConfiguration(CompleteRequestSettings settings)
    {
        Verify.NotNull(settings);
        this.RequestSettings = settings;
        return this;
    }

    /// <inheritdoc/>
    public override async Task<FunctionInvokingEventArgs> PrepareEventArgsAsync(SKContext context, FunctionInvokingEventArgs? eventArgs = null)
    {
        this.AddDefaultValues(context.Variables);
        var renderedPrompt = await this.RenderPromptTemplateAsync(context, CancellationToken.None).ConfigureAwait(false);
        context.InternalVariables.Set(RenderedPromptKey, renderedPrompt);

        return new SemanticFunctionInvokingEventArgs(this.Describe(), context);
    }

    /// <inheritdoc/>
    public override Task<FunctionInvokedEventArgs> PrepareEventArgsAsync(SKContext context, FunctionInvokedEventArgs? eventArgs = null)
    {
        return Task.FromResult<FunctionInvokedEventArgs>(new SemanticFunctionInvokedEventArgs(this.Describe(), context));
    }

    /// <summary>
    /// Dispose of resources.
    /// </summary>
    public void Dispose()
    {
        if (this._aiService is { IsValueCreated: true } aiService)
        {
            (aiService.Value as IDisposable)?.Dispose();
        }
    }

    internal SemanticFunction(
        IPromptTemplate template,
        string skillName,
        string functionName,
        string description,
        ILoggerFactory? loggerFactory = null)
        : base(
            functionName,
            skillName,
            description,
            template.GetParameters(),
            loggerFactory?.CreateLogger(nameof(SemanticFunction)) ?? NullLogger.Instance)
    {
        Verify.NotNull(template);

        this.PromptTemplate = template;
    }

    #region private

    private IReadOnlySkillCollection? _skillCollection;
    private Lazy<ITextCompletion>? _aiService = null;

    private static async Task<string> GetCompletionsResultContentAsync(IReadOnlyList<ITextResult> completions, CancellationToken cancellationToken = default)
    {
        // To avoid any unexpected behavior we only take the first completion result (when running from the Kernel)
        return await completions[0].GetCompletionAsync(cancellationToken).ConfigureAwait(false);
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => $"{this.Name} ({this.Description})";
    #endregion

    internal const string RenderedPromptKey = "RENDERED_PROMPT";

    /// <summary>Add default values to the context variables if the variable is not defined</summary>
    internal void AddDefaultValues(ContextVariables variables)
    {
        foreach (var parameter in this.Parameters)
        {
            if (!variables.ContainsKey(parameter.Name) && parameter.DefaultValue != null)
            {
                variables[parameter.Name] = parameter.DefaultValue;
            }
        }
    }

    internal Task<string> RenderPromptTemplateAsync(SKContext context, CancellationToken cancellationToken)
    {
        return this.PromptTemplate!.RenderAsync(context, cancellationToken);
    }

    internal async Task<SKContext> RunPromptAsync(
        ITextCompletion? client,
        CompleteRequestSettings? requestSettings,
        SKContext context,
        string renderedPrompt,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(client);
        Verify.NotNull(requestSettings);

        try
        {
           var completionResults = await client.GetCompletionsAsync(renderedPrompt, requestSettings, cancellationToken).ConfigureAwait(false);
            string completion = await GetCompletionsResultContentAsync(completionResults, cancellationToken).ConfigureAwait(false);

            // Update the result with the completion
            context.Variables.Update(completion);

            context.ModelResults = completionResults.Select(c => c.ModelResult).ToArray();
        }
        catch (AIException ex)
        {
            const string Message = "Something went wrong while rendering the semantic function" +
                                   " or while executing the text completion. Function: {0}.{1}. Error: {2}. Details: {3}";
            this.Logger?.LogError(ex, Message, this.SkillName, this.Name, ex.Message, ex.Detail);
            throw;
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            const string Message = "Something went wrong while rendering the semantic function" +
                                   " or while executing the text completion. Function: {0}.{1}. Error: {2}";
            this.Logger?.LogError(ex, Message, this.SkillName, this.Name, ex.Message);
            throw;
        }

        return context;
    }
}
