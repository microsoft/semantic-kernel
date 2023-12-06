// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel;

/// <summary>Provides a builder for constructing instances of <see cref="Kernel"/>.</summary>
public sealed class KernelBuilder : IKernelBuilder
{
    /// <summary>Whether to allow <see cref="Build"/>.</summary>
    /// <remarks>
    /// When the <see cref="KernelBuilder"/> is directly created by the user, this is true.
    /// When it's created by <see cref="KernelExtensions.AddKernel"/> over an existing
    /// <see cref="IServiceCollection"/>, we currently don't want to allow <see cref="Build"/>
    /// to call BuildServiceProvider, as that can lead to confusion around how other services
    /// registered in that service collection behave.
    /// </remarks>
    private readonly bool _supportsBuild = true;
    /// <summary>The collection of services to be available through the <see cref="Kernel"/>.</summary>
    private IServiceCollection? _services;
    /// <summary>A facade on top of <see cref="_services"/> for adding plugins to the services collection.</summary>
    private KernelBuilderPlugins? _plugins;

    /// <summary>Initializes a new instance of the <see cref="KernelBuilder"/>.</summary>
    public KernelBuilder() { }

    /// <summary>Initializes a new instance of the <see cref="KernelBuilder"/>.</summary>
    /// <param name="services">
    /// The <see cref="IServiceCollection"/> to wrap and use for building the <see cref="Kernel"/>.
    /// </param>
    /// <remarks>
    /// As the service collection is externally provided, <see cref="Build"/> is disabled
    /// to avoid unexpected confusion with multiple builds of the same service collection.
    /// </remarks>
    internal KernelBuilder(IServiceCollection services)
    {
        Verify.NotNull(services);

        this._services = services;
        this._supportsBuild = false;
    }

    /// <summary>Gets the collection of services to be built into the <see cref="Kernel"/>.</summary>
    public IServiceCollection Services => this._services ??= new ServiceCollection();

    /// <summary>Gets a builder for plugins to be built as services into the <see cref="Kernel"/>.</summary>
    public IKernelBuilderPlugins Plugins => this._plugins ??= new(this.Services);

    /// <summary>Constructs a new instance of <see cref="Kernel"/> using all of the settings configured on the builder.</summary>
    /// <returns>The new <see cref="Kernel"/> instance.</returns>
    /// <remarks>
    /// Every call to <see cref="Build"/> produces a new <see cref="Kernel"/> instance. The resulting <see cref="Kernel"/>
    /// instances will not share the same plugins collection or services provider (unless there are no services).
    /// </remarks>
    public Kernel Build()
    {
        if (!this._supportsBuild)
        {
            throw new InvalidOperationException("Build is not supported on this instance. Use BuildServiceProvider on the original IServiceCollection.");
        }

        IServiceProvider serviceProvider = EmptyServiceProvider.Instance;
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
            services.AddKeyedSingleton(Kernel.KernelServiceTypeToKeyMappings, typeToKeyMappings);

            serviceProvider = services.BuildServiceProvider();
        }

        return new Kernel(serviceProvider);
    }

    private sealed class KernelBuilderPlugins : IKernelBuilderPlugins
    {
        public KernelBuilderPlugins(IServiceCollection services) => this.Services = services;

        public IServiceCollection Services { get; }
    }
}
