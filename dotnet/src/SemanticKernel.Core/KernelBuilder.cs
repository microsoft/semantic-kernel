// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A builder for Semantic Kernel.
/// </summary>
public sealed class KernelBuilder
{
    private ILoggerFactory _loggerFactory = NullLoggerFactory.Instance;
    private IDelegatingHandlerFactory _httpHandlerFactory = NullHttpHandlerFactory.Instance;
    private readonly AIServiceCollection _aiServices = new();
    private IAIServiceSelector? _serviceSelector;

    /// <summary>
    /// Create a new kernel instance
    /// </summary>
    /// <returns>New kernel instance</returns>
    public static Kernel Create()
    {
        var builder = new KernelBuilder();
        return builder.Build();
    }

    /// <summary>
    /// Build a new kernel instance using the settings passed so far.
    /// </summary>
    /// <returns>Kernel instance</returns>
    public Kernel Build()
    {
#pragma warning disable CS8604 // Possible null reference argument.
        var instance = new Kernel(
            this._aiServices.Build(),
            new SKPluginCollection(),
            this._serviceSelector,
            this._httpHandlerFactory,
            this._loggerFactory
        );
#pragma warning restore CS8604 // Possible null reference argument.

        return instance;
    }

    /// <summary>
    /// Add a logger to the kernel to be built.
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>Updated kernel builder including the logger.</returns>
    public KernelBuilder WithLoggerFactory(ILoggerFactory loggerFactory)
    {
        Verify.NotNull(loggerFactory);
        this._loggerFactory = loggerFactory;
        return this;
    }

    /// <summary>
    /// Add a http handler factory to the kernel to be built.
    /// </summary>
    /// <param name="httpHandlerFactory">Http handler factory to add.</param>
    /// <returns>Updated kernel builder including the http handler factory.</returns>
    public KernelBuilder WithHttpHandlerFactory(IDelegatingHandlerFactory httpHandlerFactory)
    {
        Verify.NotNull(httpHandlerFactory);
        this._httpHandlerFactory = httpHandlerFactory;
        return this;
    }

    /// <summary>
    /// Adds a <typeparamref name="TService"/> instance to the services collection
    /// </summary>
    /// <param name="instance">The <typeparamref name="TService"/> instance.</param>
    public KernelBuilder WithDefaultAIService<TService>(TService instance) where TService : IAIService
    {
        this._aiServices.SetService<TService>(instance);
        return this;
    }

    /// <summary>
    /// Adds a <typeparamref name="TService"/> factory method to the services collection
    /// </summary>
    /// <param name="factory">The factory method that creates the AI service instances of type <typeparamref name="TService"/>.</param>
    public KernelBuilder WithDefaultAIService<TService>(Func<ILoggerFactory, TService> factory) where TService : IAIService
    {
        this._aiServices.SetService<TService>(() => factory(this._loggerFactory));
        return this;
    }

    /// <summary>
    /// Adds a <typeparamref name="TService"/> instance to the services collection
    /// </summary>
    /// <param name="serviceId">The service ID</param>
    /// <param name="instance">The <typeparamref name="TService"/> instance.</param>
    /// <param name="setAsDefault">Optional: set as the default AI service for type <typeparamref name="TService"/></param>
    public KernelBuilder WithAIService<TService>(
        string? serviceId,
        TService instance,
        bool setAsDefault = false) where TService : IAIService
    {
        this._aiServices.SetService<TService>(serviceId, instance, setAsDefault);
        return this;
    }

    /// <summary>
    /// Adds a <typeparamref name="TService"/> factory method to the services collection
    /// </summary>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates the AI service instances of type <typeparamref name="TService"/>.</param>
    /// <param name="setAsDefault">Optional: set as the default AI service for type <typeparamref name="TService"/></param>
    public KernelBuilder WithAIService<TService>(
        string? serviceId,
        Func<ILoggerFactory, TService> factory,
        bool setAsDefault = false) where TService : IAIService
    {
        this._aiServices.SetService<TService>(serviceId, () => factory(this._loggerFactory), setAsDefault);
        return this;
    }

    /// <summary>
    /// Adds a <typeparamref name="TService"/> factory method to the services collection
    /// </summary>
    /// <param name="serviceId">The service ID</param>
    /// <param name="factory">The factory method that creates the AI service instances of type <typeparamref name="TService"/>.</param>
    /// <param name="setAsDefault">Optional: set as the default AI service for type <typeparamref name="TService"/></param>
    public KernelBuilder WithAIService<TService>(
        string? serviceId,
        Func<ILoggerFactory, IDelegatingHandlerFactory, TService> factory,
        bool setAsDefault = false) where TService : IAIService
    {
        this._aiServices.SetService<TService>(serviceId, () => factory(this._loggerFactory, this._httpHandlerFactory), setAsDefault);
        return this;
    }

    /// <summary>
    /// Adds a <cref name="IAIServiceSelector"/> to the builder
    /// </summary>
    public KernelBuilder WithAIServiceSelector(IAIServiceSelector serviceSelector)
    {
        this._serviceSelector = serviceSelector;
        return this;
    }
}
