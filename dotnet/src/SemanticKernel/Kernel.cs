// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
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
    public KernelConfig Config { get; }

    /// <inheritdoc/>
    public ILogger Log { get; }

    /// <inheritdoc/>
    public ISemanticTextMemory Memory => this._memory;

    /// <inheritdoc/>
    public IReadOnlySkillCollection Skills => this._skillCollection.ReadOnlySkillCollection;

    /// <inheritdoc/>
    public IPromptTemplateEngine PromptTemplateEngine { get; }

    /// <summary>
    /// Return a new instance of the kernel builder, used to build and configure kernel instances.
    /// </summary>
    public static KernelBuilder Builder => new();

    /// <summary>
    /// Kernel constructor. See KernelBuilder for an easier and less error prone approach to create kernel instances.
    /// </summary>
    /// <param name="skillCollection"></param>
    /// <param name="promptTemplateEngine"></param>
    /// <param name="memory"></param>
    /// <param name="config"></param>
    /// <param name="log"></param>
    public Kernel(
        ISkillCollection skillCollection,
        IPromptTemplateEngine promptTemplateEngine,
        ISemanticTextMemory memory,
        KernelConfig config,
        ILogger log)
    {
        this.Log = log;
        this.Config = config;
        this.PromptTemplateEngine = promptTemplateEngine;
        this._memory = memory;
        this._skillCollection = skillCollection;
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
    public IDictionary<string, ISKFunction> ImportSkill(object skillInstance, string skillName = "")
    {
        if (string.IsNullOrWhiteSpace(skillName))
        {
            skillName = SkillCollection.GlobalSkill;
            this.Log.LogTrace("Importing skill {0} in the global namespace", skillInstance.GetType().FullName);
        }
        else
        {
            this.Log.LogTrace("Importing skill {0}", skillName);
        }

        Dictionary<string, ISKFunction> skill = ImportSkill(skillInstance, skillName, this.Log);
        foreach (KeyValuePair<string, ISKFunction> f in skill)
        {
            f.Value.SetDefaultSkillCollection(this.Skills);
            this._skillCollection.AddFunction(f.Value);
        }

        return skill;
    }

    /// <inheritdoc/>
    public ISKFunction RegisterCustomFunction(string skillName, ISKFunction customFunction)
    {
        // Future-proofing the name not to contain special chars
        Verify.ValidSkillName(skillName);
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
        var context = new SKContext(
            variables,
            this._memory,
            this._skillCollection.ReadOnlySkillCollection,
            this.Log,
            cancellationToken);

        int pipelineStepCount = -1;
        foreach (ISKFunction f in pipeline)
        {
            if (context.ErrorOccurred)
            {
                this.Log.LogError(
                    context.LastException,
                    "Something went wrong in pipeline step {0}:'{1}'", pipelineStepCount, context.LastErrorDescription);
                return context;
            }

            pipelineStepCount++;

            try
            {
                context.CancellationToken.ThrowIfCancellationRequested();
                context = await f.InvokeAsync(context).ConfigureAwait(false);

                if (context.ErrorOccurred)
                {
                    this.Log.LogError("Function call fail during pipeline step {0}: {1}.{2}. Error: {3}",
                        pipelineStepCount, f.SkillName, f.Name, context.LastErrorDescription);
                    return context;
                }
            }
            catch (Exception e) when (!e.IsCriticalException())
            {
                this.Log.LogError(e, "Something went wrong in pipeline step {0}: {1}.{2}. Error: {3}",
                    pipelineStepCount, f.SkillName, f.Name, e.Message);
                context.Fail(e.Message, e);
                return context;
            }
        }

        return context;
    }

    /// <inheritdoc/>
    public ISKFunction Func(string skillName, string functionName)
    {
        return this.Skills.GetFunction(skillName, functionName);
    }

    /// <inheritdoc/>
    public SKContext CreateNewContext(CancellationToken cancellationToken = default)
    {
        return new SKContext(
            memory: this._memory,
            skills: this._skillCollection.ReadOnlySkillCollection,
            logger: this.Log,
            cancellationToken: cancellationToken);
    }

    /// <inheritdoc/>
    public T GetService<T>(string? name = null)
    {
        // TODO: use .NET ServiceCollection (will require a lot of changes)
        // TODO: support Connectors, IHttpFactory and IDelegatingHandlerFactory

        if (typeof(T) == typeof(ITextCompletion))
        {
            name ??= this.Config.DefaultServiceId;

            if (!this.Config.TextCompletionServices.TryGetValue(name, out Func<IKernel, ITextCompletion> factory))
            {
                throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, $"'{name}' text completion service not available");
            }

            var service = factory.Invoke(this);
            return (T)service;
        }

        if (typeof(T) == typeof(IEmbeddingGeneration<string, float>))
        {
            name ??= this.Config.DefaultServiceId;

            if (!this.Config.TextEmbeddingGenerationServices.TryGetValue(name, out Func<IKernel, IEmbeddingGeneration<string, float>> factory))
            {
                throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, $"'{name}' text embedding service not available");
            }

            var service = factory.Invoke(this);
            return (T)service;
        }

        if (typeof(T) == typeof(IChatCompletion))
        {
            name ??= this.Config.DefaultServiceId;

            if (!this.Config.ChatCompletionServices.TryGetValue(name, out Func<IKernel, IChatCompletion> factory))
            {
                throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, $"'{name}' chat completion service not available");
            }

            var service = factory.Invoke(this);
            return (T)service;
        }

        if (typeof(T) == typeof(IImageGeneration))
        {
            name ??= this.Config.DefaultServiceId;

            if (!this.Config.ImageGenerationServices.TryGetValue(name, out Func<IKernel, IImageGeneration> factory))
            {
                throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, $"'{name}' image generation service not available");
            }

            var service = factory.Invoke(this);
            return (T)service;
        }

        throw new NotSupportedException("The kernel service collection doesn't support the type " + typeof(T).FullName);
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

    private ISKFunction CreateSemanticFunction(
        string skillName,
        string functionName,
        SemanticFunctionConfig functionConfig)
    {
        if (!functionConfig.PromptTemplateConfig.Type.Equals("completion", StringComparison.OrdinalIgnoreCase))
        {
            throw new AIException(
                AIException.ErrorCodes.FunctionTypeNotSupported,
                $"Function type not supported: {functionConfig.PromptTemplateConfig}");
        }

        ISKFunction func = SKFunction.FromSemanticConfig(skillName, functionName, functionConfig, this.Log);

        // Connect the function to the current kernel skill collection, in case the function
        // is invoked manually without a context and without a way to find other functions.
        func.SetDefaultSkillCollection(this.Skills);

        func.SetAIConfiguration(CompleteRequestSettings.FromCompletionConfig(functionConfig.PromptTemplateConfig.Completion));

        // Note: the service is instantiated using the kernel configuration state when the function is invoked
        func.SetAIService(() => this.GetService<ITextCompletion>());

        return func;
    }

    /// <summary>
    /// Import a skill into the kernel skill collection, so that semantic functions and pipelines can consume its functions.
    /// </summary>
    /// <param name="skillInstance">Skill class instance</param>
    /// <param name="skillName">Skill name, used to group functions under a shared namespace</param>
    /// <param name="log">Application logger</param>
    /// <returns>Dictionary of functions imported from the given class instance, case-insensitively indexed by name.</returns>
    private static Dictionary<string, ISKFunction> ImportSkill(object skillInstance, string skillName, ILogger log)
    {
        log.LogTrace("Importing skill name: {0}", skillName);
        MethodInfo[] methods = skillInstance.GetType().GetMethods(BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public);
        log.LogTrace("Methods found {0}", methods.Length);

        // Filter out null functions and fail if two functions have the same name
        Dictionary<string, ISKFunction> result = new(StringComparer.OrdinalIgnoreCase);
        foreach (MethodInfo method in methods)
        {
            if (SKFunction.FromNativeMethod(method, skillInstance, skillName, log) is ISKFunction function)
            {
                if (result.ContainsKey(function.Name))
                {
                    throw new KernelException(
                        KernelException.ErrorCodes.FunctionOverloadNotSupported,
                        "Function overloads are not supported, please differentiate function names");
                }

                result.Add(function.Name, function);
            }
        }

        log.LogTrace("Methods imported {0}", result.Count);

        return result;
    }

    #endregion
}
