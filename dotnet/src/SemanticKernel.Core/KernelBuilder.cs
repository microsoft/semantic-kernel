// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

#pragma warning disable CA1200 // Avoid using cref tags with a prefix

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides a builder for constructing instances of <see cref="Kernel"/> with a specified set of services.
/// </summary>
/// <remarks>
/// A <see cref="Kernel"/> is primarily a collection of services and plugins. Services are represented
/// via the standard <see cref="IServiceProvider"/> interface, and plugins via a <see cref="KernelPluginCollection"/>.
/// <see cref="KernelBuilder"/> makes it easy to compose those services via a fluent
/// interface. In particular, <see cref="ConfigureServices"/> allows for extension methods off of
/// <see cref="IServiceCollection"/> to be used to register services. Once composed, the builder's
/// <see cref="Build"/> method produces a new <see cref="Kernel"/> instance. The <see cref="Kernel"/>
/// exposes a <see cref="Kernel.Plugins"/> property that returns a mutable <see cref="KernelPluginCollection"/>
/// such that plugins can be added after the kernel has been built.
/// </remarks>
public sealed class KernelBuilder
{
    /// <summary>The collection of services to be available through the <see cref="Kernel"/>.</summary>
    private ServiceCollection? _services;

    /// <summary>Initializes a new instance of the <see cref="KernelBuilder"/>.</summary>
    public KernelBuilder() { }

    /// <summary>Constructs a new instance of <see cref="Kernel"/> using all of the settings configured on the builder.</summary>
    /// <returns>The new <see cref="Kernel"/> instance.</returns>
    /// <remarks>
    /// Every call to <see cref="Build"/> produces a new <see cref="Kernel"/> instance. The resulting <see cref="Kernel"/>
    /// instances will not share the same plugins collection or services provider (unless there are no services, in which
    /// case they may share an empty services singleton).
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
            Dictionary<Type, HashSet<object?>> typeToKeyMappings = new();
            foreach (ServiceDescriptor serviceDescriptor in services)
            {
                if (!typeToKeyMappings.TryGetValue(serviceDescriptor.ServiceType, out HashSet<object?>? keys))
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

        return new Kernel(serviceProvider);
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
