// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Http;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A builder for Semantic Kernel.
/// TODO: unit tests
/// </summary>
public sealed class KernelBuilder
{
    private KernelConfig _config = new();
    private ISemanticTextMemory _memory = NullMemory.Instance;
    private IMemoryStore? _memoryStorage = null;

    public KernelBuilder()
    {
        this.AddDefaultKernelServices();
    }

    /// <summary>
    /// Create a new kernel instance
    /// </summary>
    /// <returns>New kernel instance</returns>
    public static IKernel Create()
    {
        var builder = new KernelBuilder();
        return builder.Build();
    }

    public void AddDefaultKernelServices()
    {
        this.Services.AddLogging();
        this.WithRetryMessageHandler(new HttpRetryConfig());
        this.Services.AddHttpClient();
    }

    /// <summary>
    /// Build a new kernel instance using the settings passed so far.
    /// </summary>
    /// <returns>Kernel instance</returns>
    public IKernel Build()
    {
        this._config.Services = this.Services.BuildServiceProvider();

        ILoggerFactory loggerFactory =
            this._config.Services.GetService<ILoggerFactory>() ??
            NullLoggerFactory.Instance;

        ILogger<IKernel> kernelLogger =
            this._config.Services.GetService<ILoggerFactory>()?.CreateLogger<IKernel>() ??
            NullLogger<IKernel>.Instance;

        var instance = new Kernel(
            new SkillCollection(loggerFactory.CreateLogger<SkillCollection>()),
            new PromptTemplateEngine(loggerFactory.CreateLogger<PromptTemplateEngine>()),
            this._memory,
            this._config,
            loggerFactory.CreateLogger<IKernel>()
        );

        // TODO: decouple this from 'UseMemory' kernel extension
        if (this._memoryStorage != null)
        {
            instance.UseMemory(this._memoryStorage);
        }

        return instance;
    }

    /// <summary>
    /// Add a logger to the kernel to be built.
    /// </summary>
    /// <param name="loggerProvider">Logger provider to add.</param>
    /// <returns>Updated kernel builder including the logger.</returns>
    public KernelBuilder WithLogger(ILoggerProvider loggerProvider)
    {
        Verify.NotNull(loggerProvider, "The logger provider instance provided is NULL");
        this.Services.AddLogging((config) => config.AddProvider(loggerProvider));
        return this;
    }

    /// <summary>
    /// Add a logger to the kernel to be built.
    /// </summary>
    /// <param name="loggerFactory">Logger provider to use.</param>
    /// <returns>Updated kernel builder including the logger.</returns>
    public KernelBuilder WithLogger(ILoggerFactory loggerFactory)
    {
        Verify.NotNull(loggerFactory, "The logger factpry instance provided is NULL");
        this.Services.AddSingleton<ILoggerFactory>(loggerFactory);
        return this;
    }

    public KernelBuilder WithLogger(ILogger _)
    {
        // TODO: Replace all callers and remove this
        return this;
    }

    /// <summary>
    /// Add a semantic text memory entity to the kernel to be built.
    /// </summary>
    /// <param name="memory">Semantic text memory entity to add.</param>
    /// <returns>Updated kernel builder including the semantic text memory entity.</returns>
    public KernelBuilder WithMemory(ISemanticTextMemory memory)
    {
        Verify.NotNull(memory, "The memory instance provided is NULL");
        this._memory = memory;
        return this;
    }

    /// <summary>
    /// Add memory storage to the kernel to be built.
    /// </summary>
    /// <param name="storage">Storage to add.</param>
    /// <returns>Updated kernel builder including the memory storage.</returns>
    public KernelBuilder WithMemoryStorage(IMemoryStore storage)
    {
        Verify.NotNull(storage, "The memory instance provided is NULL");
        this._memoryStorage = storage;
        return this;
    }

    /// <summary>
    /// Add memory storage and an embedding generator to the kernel to be built.
    /// </summary>
    /// <param name="storage">Storage to add.</param>
    /// <param name="embeddingGenerator">Embedding generator to add.</param>
    /// <returns>Updated kernel builder including the memory storage and embedding generator.</returns>
    public KernelBuilder WithMemoryStorageAndTextEmbeddingGeneration(
        IMemoryStore storage, IEmbeddingGeneration<string, float> embeddingGenerator)
    {
        Verify.NotNull(storage, "The memory instance provided is NULL");
        Verify.NotNull(embeddingGenerator, "The embedding generator instance provided is NULL");
        this._memory = new SemanticTextMemory(storage, embeddingGenerator);
        return this;
    }

    /// <summary>
    /// Add an HTTP message handler builder to the kernel to be built.
    /// </summary>
    /// <param name="messageHandlerBuilder">HTTP message handler builder to add.</param>
    /// <returns>Updated kernel builder including the message handler factory.</returns>
    public KernelBuilder WithMessageHandlerBuilder(HttpMessageHandlerBuilder messageHandlerBuilder)
    {
        Verify.NotNull(messageHandlerBuilder, "The HTTP message handler builder instance provided is NULL");
        this.Services.AddTransient<HttpMessageHandlerBuilder>((sp) => messageHandlerBuilder);
        return this;
    }

    /// <summary>
    /// Add a retry handler to the kernel to be built.
    /// </summary>
    /// <param name="retryConfig">Config for the retry message handler.</param>
    /// <returns>Updated kernel builder including the retry handler factory.</returns>
    public KernelBuilder WithRetryMessageHandler(HttpRetryConfig retryConfig)
    {
        Verify.NotNull(retryConfig, "The retry handler instance provided is NULL");
        this.Services.AddTransient((sp) =>
        {
            ILoggerFactory logFactory =
                sp.GetService<ILoggerFactory>() ??
                NullLoggerFactory.Instance;

            return new DefaultHttpRetryHandlerFactory(retryConfig, logFactory);
        });
        
        return this;
    }

    /// <summary>
    /// Use the given configuration with the kernel to be built.
    /// </summary>
    /// <param name="config">Configuration to use.</param>
    /// <returns>Updated kernel builder including the given configuration.</returns>
    public KernelBuilder WithConfiguration(KernelConfig config)
    {
        Verify.NotNull(config, "The configuration instance provided is NULL");
        this._config = config;
        return this;
    }

    public IServiceCollection Services { get; } = new ServiceCollection();

    /// <summary>
    /// Update the configuration using the instructions provided.
    /// </summary>
    /// <param name="configure">Action that updates the current configuration.</param>
    /// <returns>Updated kernel builder including the updated configuration.</returns>
    public KernelBuilder Configure(Action<KernelConfig> configure)
    {
        Verify.NotNull(configure, "The configuration action provided is NULL");
        configure.Invoke(this._config);
        return this;
    }
}
