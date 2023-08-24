// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A builder for Semantic Kernel.
/// </summary>
public sealed class KernelBuilder
{
    private KernelConfig _config = new();
    private Func<ISemanticTextMemory> _memoryFactory = () => NullMemory.Instance;
    private ILoggerFactory _loggerFactory = NullLoggerFactory.Instance;
    private Func<IMemoryStore>? _memoryStorageFactory = null;
    private IDelegatingHandlerFactory? _httpHandlerFactory = null;
    private IPromptTemplateEngine? _promptTemplateEngine;
    private readonly AIServiceCollection _aiServices = new();

    private static bool _promptTemplateEngineInit = false;
    private static Type? _promptTemplateEngineType = null;

    /// <summary>
    /// Create a new kernel instance
    /// </summary>
    /// <returns>New kernel instance</returns>
    public static IKernel Create()
    {
        var builder = new KernelBuilder();
        return builder.Build();
    }

    /// <summary>
    /// Build a new kernel instance using the settings passed so far.
    /// </summary>
    /// <returns>Kernel instance</returns>
    public IKernel Build()
    {
        if (this._httpHandlerFactory != null)
        {
            this._config.SetHttpRetryHandlerFactory(this._httpHandlerFactory);
        }

        var instance = new Kernel(
            new SkillCollection(this._loggerFactory),
            this._aiServices.Build(),
            this._promptTemplateEngine ?? this.CreateDefaultPromptTemplateEngine(this._loggerFactory),
            this._memoryFactory.Invoke(),
            this._config,
            this._loggerFactory
        );

        // TODO: decouple this from 'UseMemory' kernel extension
        if (this._memoryStorageFactory != null)
        {
            instance.UseMemory(this._memoryStorageFactory.Invoke());
        }

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
    /// Add a semantic text memory entity to the kernel to be built.
    /// </summary>
    /// <param name="memory">Semantic text memory entity to add.</param>
    /// <returns>Updated kernel builder including the semantic text memory entity.</returns>
    public KernelBuilder WithMemory(ISemanticTextMemory memory)
    {
        Verify.NotNull(memory);
        this._memoryFactory = () => memory;
        return this;
    }

    /// <summary>
    /// Add a semantic text memory store factory.
    /// </summary>
    /// <param name="factory">The store factory.</param>
    /// <returns>Updated kernel builder including the semantic text memory entity.</returns>
    public KernelBuilder WithMemory<TStore>(Func<ILoggerFactory, KernelConfig, TStore> factory) where TStore : ISemanticTextMemory
    {
        Verify.NotNull(factory);
        this._memoryFactory = () => factory(this._loggerFactory, this._config);
        return this;
    }

    /// <summary>
    /// Add memory storage to the kernel to be built.
    /// </summary>
    /// <param name="storage">Storage to add.</param>
    /// <returns>Updated kernel builder including the memory storage.</returns>
    public KernelBuilder WithMemoryStorage(IMemoryStore storage)
    {
        Verify.NotNull(storage);
        this._memoryStorageFactory = () => storage;
        return this;
    }

    /// <summary>
    /// Add memory storage factory to the kernel.
    /// </summary>
    /// <param name="factory">The storage factory.</param>
    /// <returns>Updated kernel builder including the memory storage.</returns>
    public KernelBuilder WithMemoryStorage<TStore>(Func<ILoggerFactory, KernelConfig, TStore> factory) where TStore : IMemoryStore
    {
        Verify.NotNull(factory);
        this._memoryStorageFactory = () => factory(this._loggerFactory, this._config);
        return this;
    }

    /// <summary>
    /// Add prompt template engine to the kernel to be built.
    /// </summary>
    /// <param name="promptTemplateEngine">Prompt template engine to add.</param>
    /// <returns>Updated kernel builder including the prompt template engine.</returns>
    public KernelBuilder WithPromptTemplateEngine(IPromptTemplateEngine promptTemplateEngine)
    {
        Verify.NotNull(promptTemplateEngine);
        this._promptTemplateEngine = promptTemplateEngine;
        return this;
    }

    /// <summary>
    /// Add a retry handler factory to the kernel to be built.
    /// </summary>
    /// <param name="httpHandlerFactory">Retry handler factory to add.</param>
    /// <returns>Updated kernel builder including the retry handler factory.</returns>
    public KernelBuilder WithRetryHandlerFactory(IDelegatingHandlerFactory httpHandlerFactory)
    {
        Verify.NotNull(httpHandlerFactory);
        this._httpHandlerFactory = httpHandlerFactory;
        return this;
    }

    /// <summary>
    /// Use the given configuration with the kernel to be built.
    /// </summary>
    /// <param name="config">Configuration to use.</param>
    /// <returns>Updated kernel builder including the given configuration.</returns>
    public KernelBuilder WithConfiguration(KernelConfig config)
    {
        Verify.NotNull(config);
        this._config = config;
        return this;
    }

    /// <summary>
    /// Update the configuration using the instructions provided.
    /// </summary>
    /// <param name="configure">Action that updates the current configuration.</param>
    /// <returns>Updated kernel builder including the updated configuration.</returns>
    public KernelBuilder Configure(Action<KernelConfig> configure)
    {
        Verify.NotNull(configure);
        configure.Invoke(this._config);
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
    /// <param name="factory">The factory method that creates the AI service instances of type <typeparamref name="TService"/>.</param>
    public KernelBuilder WithDefaultAIService<TService>(Func<ILoggerFactory, TService> factory) where TService : IAIService
    {
        this._aiServices.SetService<TService>(() => factory(this._loggerFactory));
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
        Func<ILoggerFactory, KernelConfig, TService> factory,
        bool setAsDefault = false) where TService : IAIService
    {
        this._aiServices.SetService<TService>(serviceId, () => factory(this._loggerFactory, this._config), setAsDefault);
        return this;
    }

    /// <summary>
    /// Create a default prompt template engine.
    /// </summary>
    /// <param name="loggerFactory">Logger factory to be used by the template engine</param>
    /// <returns></returns>
    private IPromptTemplateEngine CreateDefaultPromptTemplateEngine(ILoggerFactory? loggerFactory = null)
    {
        if (!_promptTemplateEngineInit)
        {
            _promptTemplateEngineType = this.GetPromptTemplateEngineType();
            _promptTemplateEngineInit = true;
        }

        if (_promptTemplateEngineType is not null)
        {
            var constructor = _promptTemplateEngineType.GetConstructor(new Type[] { typeof(ILoggerFactory) });
            if (constructor is not null)
            {
#pragma warning disable CS8601 // Null logger factory is OK
                return (IPromptTemplateEngine)constructor.Invoke(new object[] { loggerFactory });
            }
        }

        return new NoopPromptTemplateEngine();
    }

    /// <summary>
    /// Get the prompt template engine type if available
    /// </summary>
    /// <returns>The type for the prompt template engine if available</returns>
    private Type? GetPromptTemplateEngineType()
    {
        try
        {
            var assembly = Assembly.Load("Microsoft.SemanticKernel.TemplateEngine");

            return assembly.ExportedTypes.Single(type =>
                type.Name.Equals("PromptTemplateEngine", StringComparison.Ordinal) &&
                type.GetInterface(nameof(IPromptTemplateEngine)) is not null);
        }
        catch (FileNotFoundException)
        {
            // Unable to load the Microsoft.SemanticKernel.TemplateEngine assembly
        }
        catch (InvalidOperationException)
        {
            // Assembly does not contain typed named PromptTemplateEngine
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            // Something unexpected by not critical
        }

        return null;
    }
}

/// <summary>
/// No-operation IPromptTemplateEngine which performs no rendering of the template.
/// </summary>
internal class NoopPromptTemplateEngine : IPromptTemplateEngine
{
    public IList<string> ExtractInputParameterNames(string? templateText)
    {
        return Enumerable.Empty<string>().ToList();
    }

    public Task<string> RenderAsync(string templateText, SKContext context, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(templateText);
    }
}
