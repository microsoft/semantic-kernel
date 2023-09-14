// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Semantic kernel class.
/// The kernel provides a skill collection to define native and semantic functions, an orchestrator to execute a list of functions.
/// Semantic functions are automatically rendered and executed using an internal prompt template rendering engine.
/// Future versions will allow to:
/// * customize the rendering engine
/// * include branching logic in the functions pipeline
/// * persist execution state for long running pipelines
/// * distribute pipelines over a network
/// * RPC functions and secure environments, e.g. sandboxing and credentials management
/// * auto-generate pipelines given a higher level goal
/// </summary>
public sealed class Kernel : IKernel, IDisposable
{
    /// <inheritdoc/>
    public ILoggerFactory LoggerFactory { get; }

    /// <inheritdoc/>
    public ISemanticTextMemory Memory => this._memory;

    /// <inheritdoc/>
    public IReadOnlySkillCollection Skills => this._skillCollection;

    /// <inheritdoc/>
    public IPromptTemplateEngine PromptTemplateEngine { get; }

    /// <summary>
    /// Return a new instance of the kernel builder, used to build and configure kernel instances.
    /// </summary>
    public static KernelBuilder Builder => new();

    /// <inheritdoc/>
    public IDelegatingHandlerFactory HttpHandlerFactory => this._httpHandlerFactory;

    /// <inheritdoc/>
    public event EventHandler<FunctionInvokingEventArgs>? FunctionInvoking;

    /// <inheritdoc/>
    public event EventHandler<FunctionInvokedEventArgs>? FunctionInvoked;

    /// <summary>
    /// Kernel constructor. See KernelBuilder for an easier and less error prone approach to create kernel instances.
    /// </summary>
    /// <param name="skillCollection">Skill collection</param>
    /// <param name="aiServiceProvider">AI Service Provider</param>
    /// <param name="promptTemplateEngine">Prompt template engine</param>
    /// <param name="memory">Semantic text Memory</param>
    /// <param name="httpHandlerFactory"></param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public Kernel(
        ISkillCollection skillCollection,
        IAIServiceProvider aiServiceProvider,
        IPromptTemplateEngine promptTemplateEngine,
        ISemanticTextMemory memory,
        IDelegatingHandlerFactory httpHandlerFactory,
        ILoggerFactory loggerFactory)
    {
        this.LoggerFactory = loggerFactory;
        this._httpHandlerFactory = httpHandlerFactory;
        this.PromptTemplateEngine = promptTemplateEngine;
        this._memory = memory;
        this._aiServiceProvider = aiServiceProvider;
        this._promptTemplateEngine = promptTemplateEngine;
        this._skillCollection = skillCollection;

        this._logger = loggerFactory.CreateLogger(typeof(Kernel));
    }

    /// <inheritdoc/>
    public ISKFunction RegisterSemanticFunction(string functionName, SemanticFunctionConfig functionConfig)
    {
        return this.RegisterSemanticFunction(SkillCollection.GlobalSkill, functionName, functionConfig);
    }

    /// <inheritdoc/>
    public ISKFunction RegisterSemanticFunction(string skillName, string functionName, SemanticFunctionConfig functionConfig)
    {
        // Future-proofing the name not to contain special chars
        Verify.ValidSkillName(skillName);
        Verify.ValidFunctionName(functionName);

        ISKFunction function = this.CreateSemanticFunction(skillName, functionName, functionConfig);
        this._skillCollection.AddFunction(function);

        return function;
    }

    /// <inheritdoc/>
    public IDictionary<string, ISKFunction> ImportSkill(object skillInstance, string? skillName = null)
    {
        Verify.NotNull(skillInstance);

        if (string.IsNullOrWhiteSpace(skillName))
        {
            skillName = SkillCollection.GlobalSkill;
            this._logger.LogTrace("Importing skill {0} in the global namespace", skillInstance.GetType().FullName);
        }
        else
        {
            this._logger.LogTrace("Importing skill {0}", skillName);
        }

        Dictionary<string, ISKFunction> skill = ImportSkill(
            skillInstance,
            skillName!,
            this._logger,
            this.LoggerFactory
        );
        foreach (KeyValuePair<string, ISKFunction> f in skill)
        {
            f.Value.SetDefaultSkillCollection(this.Skills);
            this._skillCollection.AddFunction(f.Value);
        }

        return skill;
    }

    /// <inheritdoc/>
    public ISKFunction RegisterCustomFunction(ISKFunction customFunction)
    {
        Verify.NotNull(customFunction);

        customFunction.SetDefaultSkillCollection(this.Skills);
        this._skillCollection.AddFunction(customFunction);

        return customFunction;
    }

    /// <inheritdoc/>
    public void RegisterMemory(ISemanticTextMemory memory)
    {
        this._memory = memory;
    }

    /// <inheritdoc/>
    public Task<SKContext> RunAsync(ISKFunction skFunction,
        ContextVariables? variables = null,
        CancellationToken cancellationToken = default)
        => this.RunAsync(variables ?? new(), cancellationToken, skFunction);

    /// <inheritdoc/>
    public Task<SKContext> RunAsync(params ISKFunction[] pipeline)
        => this.RunAsync(new ContextVariables(), pipeline);

    /// <inheritdoc/>
    public Task<SKContext> RunAsync(string input, params ISKFunction[] pipeline)
        => this.RunAsync(new ContextVariables(input), pipeline);

    /// <inheritdoc/>
    public Task<SKContext> RunAsync(ContextVariables variables, params ISKFunction[] pipeline)
        => this.RunAsync(variables, CancellationToken.None, pipeline);

    /// <inheritdoc/>
    public Task<SKContext> RunAsync(CancellationToken cancellationToken, params ISKFunction[] pipeline)
        => this.RunAsync(new ContextVariables(), cancellationToken, pipeline);

    /// <inheritdoc/>
    public Task<SKContext> RunAsync(string input, CancellationToken cancellationToken, params ISKFunction[] pipeline)
        => this.RunAsync(new ContextVariables(input), cancellationToken, pipeline);

    /// <inheritdoc/>
    public async Task<SKContext> RunAsync(ContextVariables variables, CancellationToken cancellationToken, params ISKFunction[] pipeline)
    {
        var context = new SKContext(this, variables);

        int pipelineStepCount = 0;
        foreach (ISKFunction skFunction in pipeline)
        {
repeat:
            cancellationToken.ThrowIfCancellationRequested();

            try
            {
                var functionDetails = skFunction.Describe();

                var functionInvokingArgs = this.OnFunctionInvoking(functionDetails, context);
                if (functionInvokingArgs?.CancelToken.IsCancellationRequested ?? false)
                {
                    this._logger.LogInformation("Execution was cancelled on function invoking event of pipeline step {StepCount}: {SkillName}.{FunctionName}.", pipelineStepCount, skFunction.SkillName, skFunction.Name);
                    break;
                }

                if (functionInvokingArgs?.IsSkipRequested ?? false)
                {
                    this._logger.LogInformation("Execution was skipped on function invoking event of pipeline step {StepCount}: {SkillName}.{FunctionName}.", pipelineStepCount, skFunction.SkillName, skFunction.Name);
                    continue;
                }

                context = await skFunction.InvokeAsync(context, cancellationToken: cancellationToken).ConfigureAwait(false);

                var functionInvokedArgs = this.OnFunctionInvoked(functionDetails, context);
                if (functionInvokedArgs?.CancelToken.IsCancellationRequested ?? false)
                {
                    this._logger.LogInformation("Execution was cancelled on function invoked event of pipeline step {StepCount}: {SkillName}.{FunctionName}.", pipelineStepCount, skFunction.SkillName, skFunction.Name);
                    break;
                }

                if (functionInvokedArgs?.IsRepeatRequested ?? false)
                {
                    this._logger.LogInformation("Execution repeat request on function invoked event of pipeline step {StepCount}: {SkillName}.{FunctionName}.", pipelineStepCount, skFunction.SkillName, skFunction.Name);
                    goto repeat;
                }
            }
            catch (Exception ex)
            {
                this._logger.LogError("Plugin {Plugin} function {Function} call fail during pipeline step {Step} with error {Error}:", skFunction.SkillName, skFunction.Name, pipelineStepCount, ex.Message);
                throw;
            }

            pipelineStepCount++;
        }

        return context;
    }

    /// <inheritdoc/>
    public ISKFunction Func(string skillName, string functionName)
    {
        return this.Skills.GetFunction(skillName, functionName);
    }

    /// <inheritdoc/>
    public SKContext CreateNewContext()
    {
        return new SKContext(
            this,
            skills: this._skillCollection,
            loggerFactory: this.LoggerFactory);
    }

    /// <inheritdoc/>
    public T GetService<T>(string? name = null) where T : IAIService
    {
        var service = this._aiServiceProvider.GetService<T>(name);
        if (service != null)
        {
            return service;
        }

        throw new SKException($"Service of type {typeof(T)} and name {name ?? "<NONE>"} not registered.");
    }

    /// <summary>
    /// Dispose of resources.
    /// </summary>
    public void Dispose()
    {
        // ReSharper disable once SuspiciousTypeConversion.Global
        if (this._memory is IDisposable mem) { mem.Dispose(); }

        // ReSharper disable once SuspiciousTypeConversion.Global
        if (this._skillCollection is IDisposable reg) { reg.Dispose(); }
    }

    #region private ================================================================================

    private readonly ISkillCollection _skillCollection;
    private ISemanticTextMemory _memory;
    private readonly IPromptTemplateEngine _promptTemplateEngine;
    private readonly IAIServiceProvider _aiServiceProvider;
    private readonly ILogger _logger;
    private readonly IDelegatingHandlerFactory _httpHandlerFactory;

    /// <summary>
    /// Execute the OnFunctionInvoking event handlers.
    /// </summary>
    /// <param name="functionView">Function view details</param>
    /// <param name="context">SKContext before function invocation</param>
    /// <returns>FunctionInvokingEventArgs if the event was handled, null otherwise</returns>
    private FunctionInvokingEventArgs? OnFunctionInvoking(FunctionView functionView, SKContext context)
    {
        if (this.FunctionInvoking is not null)
        {
            var args = new FunctionInvokingEventArgs(functionView, context);
            this.FunctionInvoking.Invoke(this, args);

            return args;
        }

        return null;
    }

    /// <summary>
    /// Execute the OnFunctionInvoked event handlers.
    /// </summary>
    /// <param name="functionView">Function view details</param>
    /// <param name="context">SKContext after function invocation</param>
    /// <returns>FunctionInvokedEventArgs if the event was handled, null otherwise</returns>
    private FunctionInvokedEventArgs? OnFunctionInvoked(FunctionView functionView, SKContext context)
    {
        if (this.FunctionInvoked is not null)
        {
            var args = new FunctionInvokedEventArgs(functionView, context);
            this.FunctionInvoked.Invoke(this, args);

            return args;
        }

        return null;
    }

    private ISKFunction CreateSemanticFunction(
        string skillName,
        string functionName,
        SemanticFunctionConfig functionConfig)
    {
        if (!functionConfig.PromptTemplateConfig.Type.Equals("completion", StringComparison.OrdinalIgnoreCase))
        {
            throw new SKException($"Function type not supported: {functionConfig.PromptTemplateConfig}");
        }

        ISKFunction func = SemanticFunction.FromSemanticConfig(
            skillName,
            functionName,
            functionConfig,
            this.LoggerFactory
        );

        // Connect the function to the current kernel skill collection, in case the function
        // is invoked manually without a context and without a way to find other functions.
        func.SetDefaultSkillCollection(this.Skills);

        func.SetAIConfiguration(CompleteRequestSettings.FromCompletionConfig(functionConfig.PromptTemplateConfig.Completion));

        // Note: the service is instantiated using the kernel configuration state when the function is invoked
        func.SetAIService(() => this.GetService<ITextCompletion>(functionConfig.PromptTemplateConfig.Completion.ServiceId));

        return func;
    }

    /// <summary>
    /// Import a skill into the kernel skill collection, so that semantic functions and pipelines can consume its functions.
    /// </summary>
    /// <param name="skillInstance">Skill class instance</param>
    /// <param name="skillName">Skill name, used to group functions under a shared namespace</param>
    /// <param name="logger">Application logger</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>Dictionary of functions imported from the given class instance, case-insensitively indexed by name.</returns>
    private static Dictionary<string, ISKFunction> ImportSkill(object skillInstance, string skillName, ILogger logger, ILoggerFactory loggerFactory)
    {
        MethodInfo[] methods = skillInstance.GetType().GetMethods(BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public);
        logger.LogTrace("Importing skill name: {0}. Potential methods found: {1}", skillName, methods.Length);

        // Filter out non-SKFunctions and fail if two functions have the same name
        Dictionary<string, ISKFunction> result = new(StringComparer.OrdinalIgnoreCase);
        foreach (MethodInfo method in methods)
        {
            if (method.GetCustomAttribute<SKFunctionAttribute>() is not null)
            {
                ISKFunction function = SKFunction.FromNativeMethod(method, skillInstance, skillName, loggerFactory);
                if (result.ContainsKey(function.Name))
                {
                    throw new SKException("Function overloads are not supported, please differentiate function names");
                }

                result.Add(function.Name, function);
            }
        }

        logger.LogTrace("Methods imported {0}", result.Count);

        return result;
    }

    #endregion
}
