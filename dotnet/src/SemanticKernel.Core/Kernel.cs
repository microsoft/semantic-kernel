// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Functions;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Semantic kernel class.
/// The kernel provides a function collection to define native and semantic functions, an orchestrator to execute a list of functions.
/// Semantic functions are automatically rendered and executed using an internal prompt template rendering engine.
/// Future versions will allow to:
/// * customize the rendering engine
/// * include branching logic in the functions pipeline
/// * persist execution state for long running pipelines
/// * distribute pipelines over a network
/// * RPC functions and secure environments, e.g. sandboxing and credentials management
/// * auto-generate pipelines given a higher level goal
/// </summary>
public sealed class Kernel
{
    /// <summary>
    /// The ILoggerFactory used to create a logger for logging.
    /// </summary>
    public ILoggerFactory LoggerFactory { get; }

    /// <summary>
    /// Reference to the read-only function collection containing all the imported functions
    /// </summary>
    public IReadOnlyFunctionCollection Functions => this._functionCollection;

    /// <summary>
    /// Return a new instance of the kernel builder, used to build and configure kernel instances.
    /// </summary>
    [Obsolete("This field will be removed in a future release. Initialize KernelBuilder through constructor instead (new KernelBuilder()).")]
    public static KernelBuilder Builder => new();

    /// <summary>
    /// Reference to Http handler factory
    /// </summary>
    public IDelegatingHandlerFactory HttpHandlerFactory { get; }

    /// <summary>
    /// Used for registering a function invoking event handler.
    /// Triggers before each function invocation.
    /// </summary>
    public event EventHandler<FunctionInvokingEventArgs>? FunctionInvoking;

    /// <summary>
    /// Used for registering a function invoked event handler.
    /// Triggers after each function invocation.
    /// </summary>
    public event EventHandler<FunctionInvokedEventArgs>? FunctionInvoked;

    /// <summary>
    /// Kernel constructor. See KernelBuilder for an easier and less error prone approach to create kernel instances.
    /// </summary>
    /// <param name="functionCollection">function collection</param>
    /// <param name="aiServiceProvider">AI Service Provider</param>
    /// <param name="promptTemplateEngine">Prompt template engine</param>
    /// <param name="memory">Semantic text Memory</param>
    /// <param name="httpHandlerFactory">HTTP handler factory</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="serviceSelector">AI Service selector</param>
    [Obsolete("Use IPromptTemplateFactory instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public Kernel(
        IFunctionCollection functionCollection,
        IAIServiceProvider aiServiceProvider,
        IPromptTemplateEngine? promptTemplateEngine,
        ISemanticTextMemory memory,
        IDelegatingHandlerFactory httpHandlerFactory,
        ILoggerFactory? loggerFactory,
        IAIServiceSelector? serviceSelector = null) : this(functionCollection, aiServiceProvider, memory, httpHandlerFactory, loggerFactory, serviceSelector)
    {
        this.PromptTemplateEngine = promptTemplateEngine ?? this.CreateDefaultPromptTemplateEngine(loggerFactory);
    }

    /// <summary>
    /// Kernel constructor. See KernelBuilder for an easier and less error prone approach to create kernel instances.
    /// </summary>
    /// <param name="functionCollection">function collection</param>
    /// <param name="aiServiceProvider">AI Service Provider</param>
    /// <param name="memory">Semantic text Memory</param>
    /// <param name="httpHandlerFactory">HTTP handler factory</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="serviceSelector">AI Service selector</param>
    [Obsolete("This constructor is obsolete and will be removed in one of the next version of SK. Please use one of the available overload.")]
    public Kernel(
        IFunctionCollection functionCollection,
        IAIServiceProvider aiServiceProvider,
        ISemanticTextMemory memory,
        IDelegatingHandlerFactory httpHandlerFactory,
        ILoggerFactory? loggerFactory,
        IAIServiceSelector? serviceSelector = null)
    {
        loggerFactory ??= NullLoggerFactory.Instance;

        this.LoggerFactory = loggerFactory;
        this.HttpHandlerFactory = httpHandlerFactory;
        this._memory = memory;
        this._aiServiceProvider = aiServiceProvider;
        this._functionCollection = functionCollection;
        this._aiServiceSelector = serviceSelector ?? new OrderedIAIServiceSelector();

        this._logger = loggerFactory.CreateLogger(typeof(Kernel));
    }

    /// <summary>
    /// Kernel constructor. See KernelBuilder for an easier and less error prone approach to create kernel instances.
    /// </summary>
    /// <param name="aiServiceProvider">AI Service Provider</param>
    /// <param name="functionCollection">function collection</param>
    /// <param name="serviceSelector">AI Service selector</param>
    /// <param name="httpHandlerFactory">HTTP handler factory</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public Kernel(
        IAIServiceProvider aiServiceProvider,
        IFunctionCollection? functionCollection = null,
        IAIServiceSelector? serviceSelector = null,
        IDelegatingHandlerFactory? httpHandlerFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        this.LoggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
        this.HttpHandlerFactory = httpHandlerFactory ?? NullHttpHandlerFactory.Instance;
        this._aiServiceProvider = aiServiceProvider;
        this._functionCollection = functionCollection ?? new FunctionCollection();
        this._aiServiceSelector = serviceSelector ?? new OrderedIAIServiceSelector();

        this._logger = this.LoggerFactory.CreateLogger(typeof(Kernel));
        this._memory = NullMemory.Instance;
    }

    /// <summary>
    /// Registers a custom function in the internal function collection.
    /// </summary>
    /// <param name="customFunction">The custom function to register.</param>
    /// <returns>A C# function wrapping the function execution logic.</returns>
    public ISKFunction RegisterCustomFunction(ISKFunction customFunction)
    {
        Verify.NotNull(customFunction);

        this._functionCollection.AddFunction(customFunction);

        return customFunction;
    }

    /// <summary>
    /// Create a new instance of a context, linked to the kernel internal state.
    /// </summary>
    /// <param name="variables">Initializes the context with the provided variables</param>
    /// <param name="functions">Provide specific scoped functions. Defaults to all existing in the kernel</param>
    /// <param name="loggerFactory">Logged factory used within the context</param>
    /// <param name="culture">Optional culture info related to the context</param>
    /// <returns>SK context</returns>
    public SKContext CreateNewContext(
        ContextVariables? variables = null,
        IReadOnlyFunctionCollection? functions = null,
        ILoggerFactory? loggerFactory = null,
        CultureInfo? culture = null)
    {
        return new SKContext(
            new FunctionRunner(this),
            this._aiServiceProvider,
            this._aiServiceSelector,
            variables,
            functions ?? this.Functions,
            new EventHandlerWrapper<FunctionInvokingEventArgs>(this.FunctionInvoking),
            new EventHandlerWrapper<FunctionInvokedEventArgs>(this.FunctionInvoked),
            loggerFactory ?? this.LoggerFactory,
            culture);
    }

    /// <summary>
    /// Get one of the configured services. Currently limited to AI services.
    /// </summary>
    /// <param name="name">Optional name. If the name is not provided, returns the default T available</param>
    /// <typeparam name="T">Service type</typeparam>
    /// <returns>Instance of T</returns>
    public T GetService<T>(string? name = null) where T : IAIService
    {
        var service = this._aiServiceProvider.GetService<T>(name);
        if (service != null)
        {
            return service;
        }

        throw new SKException($"Service of type {typeof(T)} and name {name ?? "<NONE>"} not registered.");
    }

    #region private ================================================================================

    private readonly IFunctionCollection _functionCollection;
    private ISemanticTextMemory _memory;
    private readonly IAIServiceProvider _aiServiceProvider;
    private readonly IAIServiceSelector _aiServiceSelector;
    private readonly ILogger _logger;

    #endregion

    #region Obsolete ===============================================================================

    /// <inheritdoc/>
    [Obsolete("Use IPromptTemplateFactory instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public IPromptTemplateEngine? PromptTemplateEngine { get; }

    /// <inheritdoc/>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release. See sample dotnet/samples/KernelSyntaxExamples/Example14_SemanticMemory.cs in the semantic-kernel repository.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public ISemanticTextMemory Memory => this._memory;

    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use Kernel.Functions instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public IReadOnlyFunctionCollection Skills => this._functionCollection;
#pragma warning restore CS1591

    /// <inheritdoc/>
    [Obsolete("Func shorthand no longer no longer supported. Use Kernel.Functions collection instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public ISKFunction Func(string pluginName, string functionName)
    {
        return this.Functions.GetFunction(pluginName, functionName);
    }

    /// <inheritdoc/>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release. See sample dotnet/samples/KernelSyntaxExamples/Example14_SemanticMemory.cs in the semantic-kernel repository.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public void RegisterMemory(ISemanticTextMemory memory)
    {
        this._memory = memory;
    }

    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use Kernel.ImportFunctions instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public IDictionary<string, ISKFunction> ImportSkill(object functionsInstance, string? pluginName = null)
    {
        return this.ImportFunctions(functionsInstance, pluginName);
    }
#pragma warning restore CS1591

    #endregion

    #region Private ====================================================================================

    private static bool s_promptTemplateEngineInitialized = false;
    private static Type? s_promptTemplateEngineType = null;

    /// <summary>
    /// Create a default prompt template engine.
    ///
    /// This is a temporary solution to avoid breaking existing clients.
    /// There will be a separate task to add support for registering instances of IPromptTemplateEngine and obsoleting the current approach.
    ///
    /// </summary>
    /// <param name="loggerFactory">Logger factory to be used by the template engine</param>
    /// <returns>Instance of <see cref="IPromptTemplateEngine"/>.</returns>
    [Obsolete("Provided for backward compatibility. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    private IPromptTemplateEngine CreateDefaultPromptTemplateEngine(ILoggerFactory? loggerFactory = null)
    {
        if (!s_promptTemplateEngineInitialized)
        {
            s_promptTemplateEngineType = this.GetPromptTemplateEngineType();
            s_promptTemplateEngineInitialized = true;
        }

        if (s_promptTemplateEngineType is not null)
        {
            var constructor = s_promptTemplateEngineType.GetConstructor(new Type[] { typeof(ILoggerFactory) });
            if (constructor is not null)
            {
#pragma warning disable CS8601 // Null logger factory is OK
                return (IPromptTemplateEngine)constructor.Invoke(new object[] { loggerFactory });
#pragma warning restore CS8601
            }
        }

        return new NullPromptTemplateEngine();
    }

    /// <summary>
    /// Get the prompt template engine type if available
    /// </summary>
    /// <returns>The type for the prompt template engine if available</returns>
    [Obsolete("Provided for backward compatibility. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    private Type? GetPromptTemplateEngineType()
    {
        try
        {
            var assembly = Assembly.Load("Microsoft.SemanticKernel.TemplateEngine.Basic");

            return assembly.ExportedTypes.Single(type =>
                type.Name.Equals("BasicPromptTemplateEngine", StringComparison.Ordinal) &&
                type.GetInterface(nameof(IPromptTemplateEngine)) is not null);
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            return null;
        }
    }

    #endregion
}

/// <summary>
/// No-operation IPromptTemplateEngine which performs no rendering of the template.
///
/// This is a temporary solution to avoid breaking existing clients.
/// </summary>
[Obsolete("This is used for backward compatibility. This will be removed in a future release.")]
[EditorBrowsable(EditorBrowsableState.Never)]
internal sealed class NullPromptTemplateEngine : IPromptTemplateEngine
{
    public Task<string> RenderAsync(string templateText, SKContext context, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(templateText);
    }
}
