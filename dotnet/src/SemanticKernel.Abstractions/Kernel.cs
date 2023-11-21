// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Threading;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;

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
    /// Culture currently associated with this context.
    /// </summary>
    public CultureInfo Culture
    {
        get => this._culture;
        set => this._culture = value ?? CultureInfo.CurrentCulture;
    }

    /// <summary>
    /// The ILoggerFactory used to create a logger for logging.
    /// </summary>
    public ILoggerFactory LoggerFactory { get; }

    /// <summary>
    /// Collection of <see cref="ISKPlugin"/>s.
    /// </summary>
    public ISKPluginCollection Plugins { get; }

    /// <summary>
    /// AI service provider
    /// </summary>
    public IAIServiceProvider ServiceProvider { get; }

    /// <summary>
    /// AIService selector implementation
    /// </summary>
    internal IAIServiceSelector ServiceSelector { get; }

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
    /// <param name="aiServiceProvider">AI Service Provider</param>
    /// <param name="plugins">The plugins.</param>
    /// <param name="serviceSelector">AI Service selector</param>
    /// <param name="httpHandlerFactory">HTTP handler factory</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public Kernel(
        IAIServiceProvider aiServiceProvider,
        ISKPluginCollection? plugins = null,
        IAIServiceSelector? serviceSelector = null,
        IDelegatingHandlerFactory? httpHandlerFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        this.ServiceProvider = aiServiceProvider;
        this.Plugins = plugins ?? new SKPluginCollection();
        this.ServiceSelector = serviceSelector ?? new OrderedIAIServiceSelector();
        this.HttpHandlerFactory = httpHandlerFactory ?? NullHttpHandlerFactory.Instance;
        this.LoggerFactory = loggerFactory ?? NullLoggerFactory.Instance;

        this._logger = this.LoggerFactory.CreateLogger(typeof(Kernel));
    }

    /// <summary>
    /// Create a new instance of a context, linked to the kernel internal state.
    /// </summary>
    /// <param name="variables">Initializes the context with the provided variables</param>
    /// <param name="plugins">Provides a collection of plugins to be available in the new context. By default, it's the full collection from the kernel.</param>
    /// <returns>SK context</returns>
    public SKContext CreateNewContext(
        ContextVariables? variables = null,
        IReadOnlySKPluginCollection? plugins = null)
    {
        return new SKContext(
            variables,
            new EventHandlerWrapper<FunctionInvokingEventArgs>(this.FunctionInvoking),
            new EventHandlerWrapper<FunctionInvokedEventArgs>(this.FunctionInvoked));
    }

    /// <summary>
    /// Get one of the configured services. Currently limited to AI services.
    /// </summary>
    /// <param name="name">Optional name. If the name is not provided, returns the default T available</param>
    /// <typeparam name="T">Service type</typeparam>
    /// <returns>Instance of T</returns>
    public T GetService<T>(string? name = null) where T : IAIService
    {
        var service = this.ServiceProvider.GetService<T>(name);
        if (service != null)
        {
            return service;
        }

        throw new SKException($"Service of type {typeof(T)} and name {name ?? "<NONE>"} not registered.");
    }

    /// <summary>
    /// Dictionary for arbitrary/ambient data associated with the kernel.
    /// </summary>
    public IDictionary<string, object?> Data =>
        this._data ??
        Interlocked.CompareExchange(ref this._data, new Dictionary<string, object?>(), null) ??
        this._data;

    #region private ================================================================================

    private readonly ILogger _logger;

    private Dictionary<string, object?>? _data;

    private CultureInfo _culture = CultureInfo.CurrentCulture;

    #endregion
}
