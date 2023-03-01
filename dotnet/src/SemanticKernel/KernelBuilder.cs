// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A builder for Semantic Kernel.
/// TODO: unit tests
/// </summary>
public sealed class KernelBuilder
{
    private KernelConfig _config = new KernelConfig();
    private ISemanticTextMemory _memory = NullMemory.Instance;
    private ILogger _log = NullLogger.Instance;
    private IMemoryStore<float>? _memoryStorage = null;

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
        Verify.NotNull(log, "The logger instance provided is NULL");
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
        Verify.NotNull(memory, "The memory instance provided is NULL");
        this._memory = memory;
        return this;
    }

    /// <summary>
    /// Add memory storage to the kernel to be built.
    /// </summary>
    /// <param name="storage">Storage to add.</param>
    /// <returns>Updated kernel builder including the memory storage.</returns>
    public KernelBuilder WithMemoryStorage(IMemoryStore<float> storage)
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
    public KernelBuilder WithMemoryStorageAndEmbeddingGenerator(
        IMemoryStore<float> storage, IEmbeddingGenerator<string, float> embeddingGenerator)
    {
        Verify.NotNull(storage, "The memory instance provided is NULL");
        Verify.NotNull(embeddingGenerator, "The embedding generator instance provided is NULL");
        this._memory = new SemanticTextMemory(storage, embeddingGenerator);
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
