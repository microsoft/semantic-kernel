// Copyright (c) Microsoft. All rights reserved.

using System;
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
    private ILogger _log = NullLogger.Instance;
    private IMemoryStore? _memoryStorage = null;
    private IDelegatingHandlerFactory? _httpHandlerFactory = null;

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
            new SkillCollection(this._log),
            new PromptTemplateEngine(this._log),
            this._memory,
            this._config,
            this._log
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
    /// <param name="log">Logger to add.</param>
    /// <returns>Updated kernel builder including the logger.</returns>
    public KernelBuilder WithLogger(ILogger log)
    {
        Verify.NotNull(log);
        this._log = log;
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
        Verify.NotNull(storage);
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
        Verify.NotNull(storage);
        Verify.NotNull(embeddingGenerator);
        this._memory = new SemanticTextMemory(storage, embeddingGenerator);
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
}
