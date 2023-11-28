// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Net.Http;
using System.Threading;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides state for use throughout a Semantic Kernel workload.
/// </summary>
/// <remarks>
/// An instance of <see cref="Kernel"/> is passed through to every function invocation and service call
/// throughout the system, providing to each the ability to access shared state and services.
/// </remarks>
public sealed class Kernel
{
    /// <summary>
    /// Gets the culture currently associated with this context.
    /// </summary>
    /// <remarks>
    /// The culture defaults to <see cref="CultureInfo.CurrentCulture"/> if not explicitly set.
    /// It may be set to another culture, such as <see cref="CultureInfo.InvariantCulture"/>,
    /// and any functions invoked within the context can consult this property for use in
    /// operations like formatting and parsing.
    /// </remarks>
    [AllowNull]
    public CultureInfo Culture
    {
        get => this._culture;
        set => this._culture = value ?? CultureInfo.CurrentCulture;
    }

    /// <summary>
    /// Gets the <see cref="ILoggerFactory"/> to use for logging.
    /// </summary>
    /// <remarks>
    /// If no logging is provided, this will be an instance that ignores all logging operations.
    /// </remarks>
    public ILoggerFactory LoggerFactory { get; }

    /// <summary>
    /// Gets the collection of plugins available through the kernel.
    /// </summary>
    public KernelPluginCollection Plugins =>
        this._plugins ??
        Interlocked.CompareExchange(ref this._plugins, new KernelPluginCollection(), null) ??
        this._plugins;

    /// <summary>
    /// Gets the service provider used to query for services available through the kernel.
    /// </summary>
    public IAIServiceProvider ServiceProvider { get; }

    /// <summary>
    /// Gets the <see cref="IAIServiceSelector"/> used to select between multiple AI services.
    /// </summary>
    internal IAIServiceSelector ServiceSelector =>
        this._serviceSelector ??
        Interlocked.CompareExchange(ref this._serviceSelector, new OrderedIAIServiceSelector(), null) ??
        this._serviceSelector;

    /// <summary>
    /// Gets the <see cref="IDelegatingHandlerFactory"/> to use when constructing <see cref="HttpClient"/>
    /// instances for use in HTTP requests.
    /// </summary>
    /// <remarks>
    /// This is typically only used as part of creating plugins and functions, as that is typically
    /// when such clients are constructed.
    /// </remarks>
    public IDelegatingHandlerFactory HttpHandlerFactory { get; }

    /// <summary>
    /// Provides an event that's raised prior to a function's invocation.
    /// </summary>
    public event EventHandler<FunctionInvokingEventArgs>? FunctionInvoking;

    /// <summary>
    /// Provides an event that's raised after a function's invocation.
    /// </summary>
    public event EventHandler<FunctionInvokedEventArgs>? FunctionInvoked;

    /// <summary>
    /// Provides an event that's raised prior to a prompt being rendered.
    /// </summary>
    public event EventHandler<PromptRenderingEventArgs>? PromptRendering;

    /// <summary>
    /// Provides an event that's raised after a prompt is rendered.
    /// </summary>
    public event EventHandler<PromptRenderedEventArgs>? PromptRendered;

    /// <summary>
    /// Initializes a new instance of <see cref="Kernel"/>.
    /// </summary>
    /// <param name="aiServiceProvider">The <see cref="IAIServiceProvider"/> used to query for services available through the kernel.</param>
    /// <param name="plugins">The collection of plugins available through the kernel. If null, an empty collection will be used.</param>
    /// <param name="serviceSelector">The <see cref="IAIServiceSelector"/> used to select between multiple AI services.</param>
    /// <param name="httpHandlerFactory">The <see cref="IDelegatingHandlerFactory"/> to use when constructing <see cref="HttpClient"/> instances for use in HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// The KernelBuilder class provides a fluent API for constructing a <see cref="Kernel"/> instance.
    /// </remarks>
    public Kernel(
        IAIServiceProvider aiServiceProvider,
        IEnumerable<IKernelPlugin>? plugins = null,
        IAIServiceSelector? serviceSelector = null,
        IDelegatingHandlerFactory? httpHandlerFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(aiServiceProvider);

        this.ServiceProvider = aiServiceProvider;
        this._plugins = plugins is not null ? new KernelPluginCollection(plugins) : null;
        this._serviceSelector = serviceSelector;
        this.HttpHandlerFactory = httpHandlerFactory ?? NullHttpHandlerFactory.Instance;
        this.LoggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
    }

    /// <summary>
    /// Clone the <see cref="Kernel"/> object to create a new instance that may be mutated without affecting the current instance.
    /// </summary>
    /// <remarks>
    /// The current instance is unmodified by this operation. The new <see cref="Kernel"/> will be initialized with:
    /// <list type="bullet">
    /// <item>
    /// The same <see cref="IAIServiceProvider"/> reference as is returned by the current instance's <see cref="Kernel.ServiceProvider"/>.</item>
    /// <item>The same <see cref="IAIServiceSelector"/> reference as is returned by the current instance's <see cref="Kernel.ServiceSelector"/>.</item>
    /// <item>The same <see cref="IDelegatingHandlerFactory"/> reference as is returned by the current instance's <see cref="Kernel.HttpHandlerFactory"/>.</item>
    /// <item>The same <see cref="ILoggerFactory"/> reference as is returned by the current instance's <see cref="Kernel.LoggerFactory"/>.</item>
    /// <item>
    /// A new <see cref="KernelPluginCollection"/> instance initialized with the same <see cref="IKernelPlugin"/> instances as are stored by the current instance's <see cref="Kernel.Plugins"/> collection.
    /// Changes to the new instance's plugin collection will not affect the current instance's plugin collection, and vice versa.
    /// </item>
    /// <item>
    /// All of the delegates registered with each event. Delegates are immutable (every time an additional delegate is added or removed, a new one is created),
    /// so changes to the new instance's event delegates will not affect the current instance's event delegates, and vice versa.
    /// </item>
    /// <item>
    /// A new <see cref="IDictionary{TKey, TValue}"/> containing all of the key/value pairs from the current instance's <see cref="Kernel.Data"/> dictionary.
    /// Any changes made to the new instance's dictionary will not affect the current instance's dictionary, and vice versa.
    /// </item>
    /// <item>The same <see cref="CultureInfo"/> reference as is returned by the current instance's <see cref="Kernel.Culture"/>.</item>
    /// </list>
    /// </remarks>
    public Kernel Clone() =>
        new(this.ServiceProvider,
            this.Plugins is { Count: > 0 } ? new KernelPluginCollection(this.Plugins) : null,
            this.ServiceSelector,
            this.HttpHandlerFactory,
            this.LoggerFactory)
        {
            FunctionInvoking = this.FunctionInvoking,
            FunctionInvoked = this.FunctionInvoked,
            _data = this._data is { Count: > 0 } ? new Dictionary<string, object?>(this._data) : null,
            _culture = this._culture,
        };

    /// <summary>
    /// Gets a configured service from the service provider.
    /// </summary>
    /// <typeparam name="T">Specifies the type of the service being requested.</typeparam>
    /// <param name="name">The name of the registered service. If a name is not provided, the default service for the specified <typeparamref name="T"/> is returned.</param>
    /// <returns>The instance of the service.</returns>
    /// <exception cref="KernelException">The specified service was not registered.</exception>
    public T GetService<T>(string? name = null) where T : IAIService =>
        this.ServiceProvider.GetService<T>(name) ??
        throw new KernelException($"Service of type {typeof(T)} and name {name ?? "<NONE>"} not registered.");

    /// <summary>
    /// Gets a dictionary for ambient data associated with the kernel.
    /// </summary>
    /// <remarks>
    /// This may be used to flow arbitrary data in and out of operations performed with this kernel instance.
    /// </remarks>
    public IDictionary<string, object?> Data =>
        this._data ??
        Interlocked.CompareExchange(ref this._data, new Dictionary<string, object?>(), null) ??
        this._data;

    #region internal ===============================================================================
    internal FunctionInvokingEventArgs? OnFunctionInvoking(KernelFunction function, ContextVariables variables)
    {
        var functionInvoking = this.FunctionInvoking;
        if (functionInvoking is null)
        {
            return null;
        }

        var eventArgs = new FunctionInvokingEventArgs(function, variables);
        functionInvoking.Invoke(this, eventArgs);
        return eventArgs;
    }

    internal FunctionInvokedEventArgs? OnFunctionInvoked(KernelFunction function, FunctionResult result)
    {
        var functionInvoked = this.FunctionInvoked;
        if (functionInvoked is null)
        {
            return null;
        }

        var eventArgs = new FunctionInvokedEventArgs(function, result);
        functionInvoked.Invoke(this, eventArgs);
        return eventArgs;
    }

    internal PromptRenderingEventArgs? OnPromptRendering(KernelFunction function, ContextVariables variables, PromptExecutionSettings? executionSettings)
    {
        var promptRendering = this.PromptRendering;
        if (promptRendering is null)
        {
            return null;
        }

        var eventArgs = new PromptRenderingEventArgs(function, variables, executionSettings);
        promptRendering.Invoke(this, eventArgs);
        return eventArgs;
    }

    internal PromptRenderedEventArgs? OnPromptRendered(KernelFunction function, ContextVariables variables, string renderedPrompt)
    {
        var promptRendered = this.PromptRendered;
        if (promptRendered is null)
        {
            return null;
        }

        var eventArgs = new PromptRenderedEventArgs(function, variables, renderedPrompt);
        promptRendered.Invoke(this, eventArgs);
        return eventArgs;
    }
    #endregion

    #region private ================================================================================

    private Dictionary<string, object?>? _data;
    private CultureInfo _culture = CultureInfo.CurrentCulture;
    private KernelPluginCollection? _plugins;
    private IAIServiceSelector? _serviceSelector;

    #endregion
}
