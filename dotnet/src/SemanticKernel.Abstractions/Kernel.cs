// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
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
    /// <summary>Key used by KernelBuilder to store type information into the service provider.</summary>
    internal const string KernelServiceTypeToKeyMappings = nameof(KernelServiceTypeToKeyMappings);

    /// <summary>Dictionary containing ambient data stored in the kernel, lazily-initialized on first access.</summary>
    private Dictionary<string, object?>? _data;
    /// <summary><see cref="CultureInfo"/> to be used by any operations that need access to the culture, a format provider, etc.</summary>
    private CultureInfo _culture = CultureInfo.InvariantCulture;
    /// <summary>The collection of plugins, initialized via the constructor or lazily-initialized on first access via <see cref="Plugins"/>.</summary>
    private KernelPluginCollection? _plugins;

    /// <summary>
    /// Initializes a new instance of <see cref="Kernel"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceProvider"/> used to query for services available through the kernel.</param>
    /// <param name="plugins">
    /// The collection of plugins available through the kernel. If null, an empty collection will be used.
    /// If non-null, the supplied collection instance is used, not a copy; if it's desired for the <see cref="Kernel"/>
    /// to have a copy, the caller is responsible for supplying it.
    /// </param>
    /// <remarks>
    /// The KernelBuilder class provides a fluent API for constructing a <see cref="Kernel"/> instance.
    /// </remarks>
    public Kernel(
        IServiceProvider? services = null,
        KernelPluginCollection? plugins = null)
    {
        // Store the provided services, or an empty singleton if there aren't any.
        this.Services = services ?? EmptyServiceProvider.Instance;

        // Store the provided plugins. If there weren't any, look in DI to see if there's a plugin collection.
        this._plugins = plugins ?? this.Services.GetService<KernelPluginCollection>();
        if (this._plugins is null)
        {
            // Otherwise, enumerate any plugins that may have been registered directly.
            IEnumerable<KernelPlugin> e = this.Services.GetServices<KernelPlugin>();

            // It'll be common not to have any plugins directly registered as a service.
            // If we can efficiently tell there aren't any, avoid proactively allocating
            // the plugins collection.
            if (e is not ICollection<KernelPlugin> c || c.Count != 0)
            {
                this._plugins = new(e);
            }
        }
    }

    /// <summary>Creates a builder for constructing <see cref="Kernel"/> instances.</summary>
    /// <returns>A new <see cref="IKernelBuilder"/> instance.</returns>
    public static IKernelBuilder CreateBuilder() => new KernelBuilder();

    /// <summary>
    /// Clone the <see cref="Kernel"/> object to create a new instance that may be mutated without affecting the current instance.
    /// </summary>
    /// <remarks>
    /// The current instance is unmodified by this operation. The new <see cref="Kernel"/> will be initialized with:
    /// <list type="bullet">
    /// <item>
    /// The same <see cref="IServiceProvider"/> reference as is returned by the current instance's <see cref="Kernel.Services"/>.
    /// </item>
    /// <item>
    /// A new <see cref="KernelPluginCollection"/> instance initialized with the same <see cref="KernelPlugin"/> instances as are stored by the current instance's <see cref="Kernel.Plugins"/> collection.
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
        new(this.Services, this._plugins is { Count: > 0 } ? new KernelPluginCollection(this._plugins) : null)
        {
            FunctionInvoking = this.FunctionInvoking,
            FunctionInvoked = this.FunctionInvoked,
            PromptRendering = this.PromptRendering,
            PromptRendered = this.PromptRendered,
            _data = this._data is { Count: > 0 } ? new Dictionary<string, object?>(this._data) : null,
            _culture = this._culture,
        };

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
    public IServiceProvider Services { get; }

    /// <summary>
    /// Gets the culture currently associated with this <see cref="Kernel"/>.
    /// </summary>
    /// <remarks>
    /// The culture defaults to <see cref="CultureInfo.InvariantCulture"/> if not explicitly set.
    /// It may be set to another culture, such as <see cref="CultureInfo.CurrentCulture"/>,
    /// and any functions invoked within the context can consult this property for use in
    /// operations like formatting and parsing.
    /// </remarks>
    [AllowNull]
    public CultureInfo Culture
    {
        get => this._culture;
        set => this._culture = value ?? CultureInfo.InvariantCulture;
    }

    /// <summary>
    /// Gets the <see cref="ILoggerFactory"/> associated with this <see cref="Kernel"/>.
    /// </summary>
    /// <remarks>
    /// This returns any <see cref="ILoggerFactory"/> in <see cref="Services"/>. If there is
    /// none, it returns an <see cref="ILoggerFactory"/> that won't perform any logging.
    /// </remarks>
    public ILoggerFactory LoggerFactory =>
        this.Services.GetService<ILoggerFactory>() ??
        NullLoggerFactory.Instance;

    /// <summary>
    /// Gets the <see cref="IAIServiceSelector"/> associated with this <see cref="Kernel"/>.
    /// </summary>
    public IAIServiceSelector ServiceSelector =>
        this.Services.GetService<IAIServiceSelector>() ??
        OrderedAIServiceSelector.Instance;

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

    /// <summary>
    /// Provides an event that's raised prior to a function's invocation.
    /// </summary>
    [Experimental("SKEXP0004")]
    public event EventHandler<FunctionInvokingEventArgs>? FunctionInvoking;

    /// <summary>
    /// Provides an event that's raised after a function's invocation.
    /// </summary>
    [Experimental("SKEXP0004")]
    public event EventHandler<FunctionInvokedEventArgs>? FunctionInvoked;

    /// <summary>
    /// Provides an event that's raised prior to a prompt being rendered.
    /// </summary>
    [Experimental("SKEXP0004")]
    public event EventHandler<PromptRenderingEventArgs>? PromptRendering;

    /// <summary>
    /// Provides an event that's raised after a prompt is rendered.
    /// </summary>
    [Experimental("SKEXP0004")]
    public event EventHandler<PromptRenderedEventArgs>? PromptRendered;

    #region GetServices
    /// <summary>Gets a required service from the <see cref="Services"/> provider.</summary>
    /// <typeparam name="T">Specifies the type of the service to get.</typeparam>
    /// <param name="serviceKey">An object that specifies the key of the service to get.</param>
    /// <returns>The found service instance.</returns>
    /// <exception cref="KernelException">A service of the specified type and name could not be found.</exception>
    public T GetRequiredService<T>(object? serviceKey = null) where T : class
    {
        T? service = null;

        if (serviceKey is not null)
        {
            if (this.Services is IKeyedServiceProvider)
            {
                // We were given a service ID, so we need to use the keyed service lookup.
                service = this.Services.GetKeyedService<T>(serviceKey);
            }
        }
        else
        {
            // No ID was given. We first want to use non-keyed lookup, in order to match against
            // a service registered without an ID. If we can't find one, then we try to match with
            // a service registered with an ID. In both cases, if there were multiple, this will match
            // with whichever was registered last.
            service = this.Services.GetService<T>();
            if (service is null && this.Services is IKeyedServiceProvider)
            {
                service = this.GetAllServices<T>().LastOrDefault();
            }
        }

        // If we couldn't find the service, throw an exception.
        if (service is null)
        {
            string message =
                serviceKey is null ? $"Service of type '{typeof(T)}' not registered." :
                this.Services is not IKeyedServiceProvider ? $"Key '{serviceKey}' specified but service provider '{this.Services}' is not a {nameof(IKeyedServiceProvider)}." :
                $"Service of type '{typeof(T)}' and key '{serviceKey}' not registered.";

            throw new KernelException(message);
        }

        // Return the found service.
        return service;
    }

    /// <summary>Gets all services of the specified type.</summary>
    /// <typeparam name="T">Specifies the type of the services to retrieve.</typeparam>
    /// <returns>An enumerable of all instances of the specified service that are registered.</returns>
    /// <remarks>There is no guaranteed ordering on the results.</remarks>
    public IEnumerable<T> GetAllServices<T>() where T : class
    {
        if (this.Services is IKeyedServiceProvider)
        {
            // M.E.DI doesn't support querying for a service without a key, and it also doesn't
            // support AnyKey currently: https://github.com/dotnet/runtime/issues/91466
            // As a workaround, KernelBuilder injects a service containing the type-to-all-keys
            // mapping. We can query for that service and and then use it to try to get a service.
            if (this.Services.GetKeyedService<Dictionary<Type, HashSet<object?>>>(KernelServiceTypeToKeyMappings) is { } typeToKeyMappings)
            {
                if (typeToKeyMappings.TryGetValue(typeof(T), out HashSet<object?> keys))
                {
                    return keys.SelectMany(key => this.Services.GetKeyedServices<T>(key));
                }

                return Enumerable.Empty<T>();
            }
        }

        return this.Services.GetServices<T>();
    }

    #endregion

    #region Internal Event Helpers
    [Experimental("SKEXP0004")]
    internal FunctionInvokingEventArgs? OnFunctionInvoking(KernelFunction function, KernelArguments arguments)
    {
        FunctionInvokingEventArgs? eventArgs = null;
        if (this.FunctionInvoking is { } functionInvoking)
        {
            eventArgs = new(function, arguments);
            functionInvoking.Invoke(this, eventArgs);
        }

        return eventArgs;
    }

    [Experimental("SKEXP0004")]
    internal FunctionInvokedEventArgs? OnFunctionInvoked(KernelFunction function, KernelArguments arguments, FunctionResult result)
    {
        FunctionInvokedEventArgs? eventArgs = null;
        if (this.FunctionInvoked is { } functionInvoked)
        {
            eventArgs = new(function, arguments, result);
            functionInvoked.Invoke(this, eventArgs);
        }

        return eventArgs;
    }

    [Experimental("SKEXP0004")]
    internal PromptRenderingEventArgs? OnPromptRendering(KernelFunction function, KernelArguments arguments)
    {
        PromptRenderingEventArgs? eventArgs = null;
        if (this.PromptRendering is { } promptRendering)
        {
            eventArgs = new(function, arguments);
            promptRendering.Invoke(this, eventArgs);
        }

        return eventArgs;
    }

    [Experimental("SKEXP0004")]
    internal PromptRenderedEventArgs? OnPromptRendered(KernelFunction function, KernelArguments arguments, string renderedPrompt)
    {
        PromptRenderedEventArgs? eventArgs = null;
        if (this.PromptRendered is { } promptRendered)
        {
            eventArgs = new(function, arguments, renderedPrompt);
            promptRendered.Invoke(this, eventArgs);
        }

        return eventArgs;
    }
    #endregion

    #region InvokeAsync

    /// <summary>
    /// Invokes the <see cref="KernelFunction"/>.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> to invoke.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function's execution.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="function"/> is null.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    /// <remarks>
    /// This behaves identically to invoking the specified <paramref name="function"/> with this <see cref="Kernel"/> as its <see cref="Kernel"/> argument.
    /// </remarks>
    public Task<FunctionResult> InvokeAsync(
        KernelFunction function,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(function);

        return function.InvokeAsync(this, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes a function from <see cref="Kernel.Plugins"/> using the specified arguments.
    /// </summary>
    /// <param name="pluginName">The name of the plugin containing the function to invoke. If null, all plugins will be searched for the first function of the specified name.</param>
    /// <param name="functionName">The name of the function to invoke.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function's execution.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="functionName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="functionName"/> is composed entirely of whitespace.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    /// <remarks>
    /// This behaves identically to using <see cref="KernelPluginExtensions.GetFunction"/> to find the desired <see cref="KernelFunction"/> and then
    /// invoking it with this <see cref="Kernel"/> as its <see cref="Kernel"/> argument.
    /// </remarks>
    public Task<FunctionResult> InvokeAsync(
        string? pluginName,
        string functionName,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(functionName);

        var function = this.Plugins.GetFunction(pluginName, functionName);

        return function.InvokeAsync(this, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes the <see cref="KernelFunction"/>.
    /// </summary>
    /// <typeparam name="TResult">Specifies the type of the result value of the function.</typeparam>
    /// <param name="function">The <see cref="KernelFunction"/> to invoke.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function's execution, cast to <typeparamref name="TResult"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="function"/> is null.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    /// <exception cref="InvalidCastException">The function's result could not be cast to <typeparamref name="TResult"/>.</exception>
    /// <remarks>
    /// This behaves identically to invoking the specified <paramref name="function"/> with this <see cref="Kernel"/> as its <see cref="Kernel"/> argument.
    /// </remarks>
    public async Task<TResult?> InvokeAsync<TResult>(
        KernelFunction function,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        FunctionResult result = await this.InvokeAsync(function, arguments, cancellationToken).ConfigureAwait(false);
        return result.GetValue<TResult>();
    }

    /// <summary>
    /// Invokes a function from <see cref="Plugins"/> using the specified arguments.
    /// </summary>
    /// <typeparam name="TResult">Specifies the type of the result value of the function.</typeparam>
    /// <param name="pluginName">The name of the plugin containing the function to invoke. If null, all plugins will be searched for the first function of the specified name.</param>
    /// <param name="functionName">The name of the function to invoke.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function's execution, cast to <typeparamref name="TResult"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="functionName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="functionName"/> is composed entirely of whitespace.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    /// <exception cref="InvalidCastException">The function's result could not be cast to <typeparamref name="TResult"/>.</exception>
    /// <remarks>
    /// This behaves identically to using <see cref="KernelPluginExtensions.GetFunction"/> to find the desired <see cref="KernelFunction"/> and then
    /// invoking it with this <see cref="Kernel"/> as its <see cref="Kernel"/> argument.
    /// </remarks>
    public async Task<TResult?> InvokeAsync<TResult>(
        string? pluginName,
        string functionName,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        FunctionResult result = await this.InvokeAsync(pluginName, functionName, arguments, cancellationToken).ConfigureAwait(false);
        return result.GetValue<TResult>();
    }

    #endregion

    #region InvokeStreamingAsync
    /// <summary>
    /// Invokes the <see cref="KernelFunction"/> and streams its results.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> to invoke.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> for streaming the results of the function's invocation.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="function"/> is null.</exception>
    /// <remarks>
    /// The function will not be invoked until an enumerator is retrieved from the returned <see cref="IAsyncEnumerable{T}"/>
    /// and its iteration initiated via an initial call to <see cref="IAsyncEnumerator{T}.MoveNextAsync"/>.
    /// </remarks>
    public IAsyncEnumerable<StreamingKernelContent> InvokeStreamingAsync(
        KernelFunction function,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(function);

        return function.InvokeStreamingAsync<StreamingKernelContent>(this, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes the <see cref="KernelFunction"/> and streams its results.
    /// </summary>
    /// <param name="pluginName">The name of the plugin containing the function to invoke. If null, all plugins will be searched for the first function of the specified name.</param>
    /// <param name="functionName">The name of the function to invoke.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> for streaming the results of the function's invocation.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="functionName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="functionName"/> is composed entirely of whitespace.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    /// <remarks>
    /// The function will not be invoked until an enumerator is retrieved from the returned <see cref="IAsyncEnumerable{T}"/>
    /// and its iteration initiated via an initial call to <see cref="IAsyncEnumerator{T}.MoveNextAsync"/>.
    /// </remarks>
    public IAsyncEnumerable<StreamingKernelContent> InvokeStreamingAsync(
        string? pluginName,
        string functionName,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(functionName);

        var function = this.Plugins.GetFunction(pluginName, functionName);

        return function.InvokeStreamingAsync<StreamingKernelContent>(this, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes the <see cref="KernelFunction"/> and streams its results.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> to invoke.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> for streaming the results of the function's invocation.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="function"/> is null.</exception>
    /// <remarks>
    /// The function will not be invoked until an enumerator is retrieved from the returned <see cref="IAsyncEnumerable{T}"/>
    /// and its iteration initiated via an initial call to <see cref="IAsyncEnumerator{T}.MoveNextAsync"/>.
    /// </remarks>
    public IAsyncEnumerable<T> InvokeStreamingAsync<T>(
        KernelFunction function,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(function);

        return function.InvokeStreamingAsync<T>(this, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes the <see cref="KernelFunction"/> and streams its results.
    /// </summary>
    /// <param name="pluginName">The name of the plugin containing the function to invoke. If null, all plugins will be searched for the first function of the specified name.</param>
    /// <param name="functionName">The name of the function to invoke.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> for streaming the results of the function's invocation.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="functionName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="functionName"/> is composed entirely of whitespace.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    /// <remarks>
    /// The function will not be invoked until an enumerator is retrieved from the returned <see cref="IAsyncEnumerable{T}"/>
    /// and its iteration initiated via an initial call to <see cref="IAsyncEnumerator{T}.MoveNextAsync"/>.
    /// </remarks>
    public IAsyncEnumerable<T> InvokeStreamingAsync<T>(
        string? pluginName,
        string functionName,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(functionName);

        var function = this.Plugins.GetFunction(pluginName, functionName);

        return function.InvokeStreamingAsync<T>(this, arguments, cancellationToken);
    }
    #endregion
}
