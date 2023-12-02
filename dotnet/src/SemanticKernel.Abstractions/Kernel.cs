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
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Events;
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
        this.Services = services ?? EmptyServiceProvider.Instance;
        this._plugins = plugins;
    }

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
    /// This behaves the same as calling <see cref="GetService{ILoggerFactory}"/>.
    /// </remarks>
    public ILoggerFactory LoggerFactory => this.GetService<ILoggerFactory>();

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

    #region GetServices
    /// <summary>Gets a service from the <see cref="Services"/> collection.</summary>
    /// <typeparam name="T">Specifies the type of the service to get.</typeparam>
    /// <param name="serviceId">An object that specifies the key of the service to get.</param>
    /// <returns>The found service instance.</returns>
    /// <exception cref="KernelException">A service of the specified type and name could not be found.</exception>
    /// <remarks>
    /// The behavior of this method is not the same as that of <see cref="IServiceProvider.GetService(Type)"/>
    /// on the exposed <see cref="Services"/>. Rather, it is opinionated view around it. If a <paramref name="serviceId"/>
    /// is provided, it will attempt to find a service registered with that key. If no <paramref name="serviceId"/>
    /// is provided, it will attempt to find any service registered, regardless of whether it was registered with
    /// with a key. If multiple services meet the criteria, it will return one of those registered, but no guarantee
    /// on exactly which. For certain services, like <see cref="ILoggerFactory"/>, it will also return a default implementation
    /// if no key was specified and no service was found. If it's able to find the specified service, that service is returned.
    /// Otherwise, an exception is thrown.
    /// </remarks>
    public T GetService<T>(string? serviceId = null) where T : class
    {
        T? service = null;

        if (serviceId is not null)
        {
            if (this.Services is IKeyedServiceProvider)
            {
                // We were given a service ID, so we need to use the keyed service lookup.
                service = this.Services.GetKeyedService<T>(serviceId);
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

            // If no service could be found, special-case specific services to provide a default.
            if (service is null)
            {
                if (typeof(T) == typeof(ILoggerFactory) || typeof(T) == typeof(NullLoggerFactory))
                {
                    return (T)(object)NullLoggerFactory.Instance;
                }

                if (typeof(T) == typeof(IAIServiceSelector) || typeof(T) == typeof(OrderedAIServiceSelector))
                {
                    return (T)(object)OrderedAIServiceSelector.Instance;
                }
            }
        }

        // If we couldn't find the service, throw an exception.
        if (service is null)
        {
            string message =
                serviceId is null ? $"Service of type '{typeof(T)}' not registered." :
                this.Services is not IKeyedServiceProvider ? $"Key '{serviceId}' specified but service provider '{this.Services}' is not a {nameof(IKeyedServiceProvider)}." :
                $"Service of type '{typeof(T)}' and key '{serviceId}' not registered.";

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

        if (this.Services is EmptyServiceProvider)
        {
            // If the Kernel is created without a service provider, it uses a simple empty implementation.
            // But the GetServices extension relies on the service provider special-casing enumerables.
            // Since the empty provider doesn't do that, we need to special-case it here.
            return Enumerable.Empty<T>();
        }

        return this.Services.GetServices<T>();
    }

    #endregion

    #region Internal Event Helpers
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
    /// Invokes a function using the specified input argument.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> to invoke.</param>
    /// <param name="input">The single argument to use as the <see cref="KernelArguments.InputParameterName"/> to the function.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of invoking the function.</returns>
    /// <remarks>
    /// This behaves identically to invoking the specified <paramref name="function"/> with this <see cref="Kernel"/> as its <see cref="Kernel"/> argument.
    /// </remarks>
    public Task<FunctionResult> InvokeAsync(
        KernelFunction function,
        string input,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(function);
        Verify.NotNull(input);

        return function.InvokeAsync(this, input, executionSettings: null, cancellationToken);
    }

    /// <summary>
    /// Invokes a function using the specified arguments.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> to invoke.</param>
    /// <param name="arguments">The arguments to pass to the invocation of <paramref name="function"/>. If null, no arguments will be supplied.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of invoking the function.</returns>
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
    /// <param name="arguments">The arguments to pass to the invocation of the function. If null, no arguments will be supplied.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of invoking the function.</returns>
    /// <remarks>
    /// This behaves identically to using <see cref="IKernelPluginExtensions.GetFunction"/> to find the desired <see cref="KernelFunction"/> and then
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
    #endregion

    #region InvokeStreamingAsync
    /// <summary>
    /// Invokes a function using the specified arguments and streaming the output contents.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> to invoke.</param>
    /// <param name="arguments">The arguments to pass to the invocation of <paramref name="function"/>. If null, no arguments will be supplied.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The streamed resulting content from invoking <paramref name="function"/>.</returns>
    public IAsyncEnumerable<StreamingContent> InvokeStreamingAsync(KernelFunction function, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(function);

        return function.InvokeStreamingAsync<StreamingContent>(this, arguments, CancellationToken.None);
    }

    /// <summary>
    /// Invokes a function using the specified arguments and streaming the output contents.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> to invoke.</param>
    /// <param name="arguments">The arguments to pass to the invocation of <paramref name="function"/>. If null, no arguments will be supplied.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The streamed resulting content from invoking <paramref name="function"/>.</returns>
    public IAsyncEnumerable<T> InvokeStreamingAsync<T>(KernelFunction function, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(function);

        return function.InvokeStreamingAsync<T>(this, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes a function using the specified input argument and streaming the output contents.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> to invoke.</param>
    /// <param name="input">The single argument to use as the <see cref="KernelArguments.InputParameterName"/> to the function.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The streamed resulting content from invoking <paramref name="function"/>.</returns>
    public IAsyncEnumerable<StreamingContent> InvokeStreamingAsync(KernelFunction function, string input, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(function);
        Verify.NotNull(input);

        return this.InvokeStreamingAsync<StreamingContent>(function, input, CancellationToken.None);
    }

    /// <summary>
    /// Invokes a function using the specified input argument and streaming the output contents.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> to invoke.</param>
    /// <param name="input">The single argument to use as the <see cref="KernelArguments.InputParameterName"/> to the function.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The streamed resulting content from invoking <paramref name="function"/>.</returns>
    public IAsyncEnumerable<T> InvokeStreamingAsync<T>(KernelFunction function, string input, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(function);
        Verify.NotNull(input);

        return function.InvokeStreamingAsync<T>(this, input, executionSettings: null, cancellationToken);
    }
    #endregion
}
