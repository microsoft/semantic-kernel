// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

#pragma warning disable CA1200 // Avoid using cref tags with a prefix

namespace Microsoft.SemanticKernel;

/// <summary>Provides a builder for constructing instances of <see cref="Kernel"/>.</summary>
/// <remarks>
/// A <see cref="Kernel"/> is primarily a collection of services and plugins. Services are represented
/// via the standard <see cref="IServiceProvider"/> interface, and plugins via a <see cref="KernelPluginCollection"/>.
/// <see cref="KernelBuilder"/> makes it easy to compose those services and plugins via a fluent
/// interface. In particular, <see cref="ConfigureServices"/> allows for extension methods off of
/// <see cref="IServiceCollection"/> to be used to register services, and <see cref="M:ConfigurePlugins"/>
/// allows for plugins to be constructed and added to the collection, having been handed a reference
/// to the <see cref="IServiceProvider"/>, in case it's needed for resolving services, e.g. a <see cref="HttpClient"/>
/// or <see cref="ILoggerFactory"/> that might be used by the plugin. Once composed, the builder's
/// <see cref="Build"/> method produces a new <see cref="Kernel"/> instance.
/// </remarks>
public sealed class KernelBuilder
{
    /// <summary>The collection of services to be available through the <see cref="Kernel"/>.</summary>
    private ServiceCollection? _services;
    /// <summary>Multicast delegate of configuration callbacks for creating plugins.</summary>
    private Action<IServiceProvider, ICollection<IKernelPlugin>>? _pluginCallbacks;
    /// <summary>The initial culture to be stored in the <see cref="Kernel"/>.</summary>
    private CultureInfo? _culture;

    /// <summary>Initializes a new instance of the <see cref="KernelBuilder"/>.</summary>
    public KernelBuilder() { }

    /// <summary>Constructs a new instance of <see cref="Kernel"/> using all of the settings configured on the builder.</summary>
    /// <returns>The new <see cref="Kernel"/> instance.</returns>
    /// <remarks>
    /// Every call to <see cref="Build"/> produces a new <see cref="Kernel"/> instance. The resulting <see cref="Kernel"/>
    /// instances will not share the same plugins collection or services provider (unless there are no services).
    /// </remarks>
    public Kernel Build()
    {
        IServiceProvider serviceProvider;
        if (this._services is { Count: > 0 } services)
        {
            // This is a workaround for Microsoft.Extensions.DependencyInjection's GetKeyedServices not currently supporting
            // enumerating all services for a given type regardless of key.
            // https://github.com/dotnet/runtime/issues/91466
            // We need this support to, for example, allow IServiceSelector to pick from multiple named instances of an AI
            // service based on their characteristics. Until that is addressed, we work around it by injecting as a service all
            // of the keys used for a given type, such that Kernel can then query for this dictionary and enumerate it. This means
            // that such functionality will work when KernelBuilder is used to build the kernel but not when the IServiceProvider
            // is created via other means, such as if Kernel is directly created by DI. However, it allows us to create the APIs
            // the way we want them for the longer term and then subsequently fix the implementation when M.E.DI is fixed.
            Dictionary<Type, List<object?>> typeToKeyMappings = new();
            foreach (ServiceDescriptor serviceDescriptor in services)
            {
                if (!typeToKeyMappings.TryGetValue(serviceDescriptor.ServiceType, out List<object?>? keys))
                {
                    typeToKeyMappings[serviceDescriptor.ServiceType] = keys = new();
                }

                keys.Add(serviceDescriptor.ServiceKey);
            }
            services.AddKeyedSingleton(Kernel.KernelServiceTypeToKeyMappingsKey, typeToKeyMappings);

            serviceProvider = services.BuildServiceProvider();
        }
        else
        {
            serviceProvider = EmptyServiceProvider.Instance;
        }

        KernelPluginCollection? plugins = null;
        if (this._pluginCallbacks is { } pluginCallbacks)
        {
            plugins = new KernelPluginCollection();
            pluginCallbacks(serviceProvider, plugins);
        }

        var instance = new Kernel(serviceProvider, plugins);

        if (this._culture != null)
        {
            instance.Culture = this._culture;
        }

        return instance;
    }

    /// <summary>
    /// Configures the services to be available through the <see cref="Kernel"/>.
    /// </summary>
    /// <param name="configureServices">Callback invoked as part of this call. It's passed the service collection to manipulate.</param>
    /// <returns>This <see cref="KernelBuilder"/> instance.</returns>
    /// <remarks>The callback will be invoked synchronously as part of the call to <see cref="ConfigureServices"/>.</remarks>
    public KernelBuilder ConfigureServices(Action<IServiceCollection> configureServices)
    {
        Verify.NotNull(configureServices);

        this._services ??= new();
        configureServices(this._services);

        return this;
    }

    /// <summary>
    /// Configures the plugins to be available through the <see cref="Kernel"/>.
    /// </summary>
    /// <param name="configurePlugins">Callback to invoke to add plugins.</param>
    /// <returns>This <see cref="KernelBuilder"/> instance.</returns>
    /// <remarks>The callback will be invoked as part of each call to <see cref="Build"/>.</remarks>
    public KernelBuilder ConfigurePlugins(Action<ICollection<IKernelPlugin>> configurePlugins)
    {
        Verify.NotNull(configurePlugins);

        this._pluginCallbacks += (_, plugins) => configurePlugins(plugins);

        return this;
    }

    /// <summary>
    /// Configures the plugins to be available through the <see cref="Kernel"/>.
    /// </summary>
    /// <param name="configurePlugins">Callback to invoke to add plugins.</param>
    /// <returns>This <see cref="KernelBuilder"/> instance.</returns>
    /// <remarks>
    /// The callback will be invoked as part of each call to <see cref="Build"/>. It is passed the same <see cref="IServiceProvider"/>
    /// that will be provided to the <see cref="Kernel"/> so that the callback can resolve services necessary to create plugins.
    /// </remarks>
    public KernelBuilder ConfigurePlugins(Action<IServiceProvider, ICollection<IKernelPlugin>> configurePlugins)
    {
        Verify.NotNull(configurePlugins);

        this._pluginCallbacks += configurePlugins;

        return this;
    }

    /// <summary>Sets a culture to be used by the <see cref="Kernel"/>.</summary>
    /// <param name="culture">The culture.</param>
    public KernelBuilder WithCulture(CultureInfo? culture)
    {
        this._culture = culture;

        return this;
    }

    /// <summary>Configures the services to contain the specified singleton <see cref="IAIServiceSelector"/>.</summary>
    /// <param name="aiServiceSelector">The <see cref="IAIServiceSelector"/> to use to select an AI service from those registered in the kernel.</param>
    /// <returns>This <see cref="KernelBuilder"/> instance.</returns>
    public KernelBuilder WithAIServiceSelector(IAIServiceSelector? aiServiceSelector) => this.WithSingleton(aiServiceSelector);

    /// <summary>Configures the services to contain the specified singleton <see cref="ILoggerFactory"/>.</summary>
    /// <param name="loggerFactory">The logger factory. If null, no logger factory will be registered.</param>
    /// <returns>This <see cref="KernelBuilder"/> instance.</returns>
    public KernelBuilder WithLoggerFactory(ILoggerFactory? loggerFactory) => this.WithSingleton(loggerFactory);

    /// <summary>Configures the services to contain the specified singleton.</summary>
    /// <typeparam name="T">Specifies the service type.</typeparam>
    /// <param name="instance">The singleton instance.</param>
    /// <returns>This <see cref="KernelBuilder"/> instance.</returns>
    private KernelBuilder WithSingleton<T>(T? instance) where T : class
    {
        if (instance is not null)
        {
            (this._services ??= new()).AddSingleton(instance);
        }

        return this;
    }
}
