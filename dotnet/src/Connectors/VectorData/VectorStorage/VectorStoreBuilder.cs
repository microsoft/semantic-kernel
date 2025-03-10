// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.VectorData;

/// <summary>A builder for creating pipelines of <see cref="IVectorStore"/>.</summary>
[Experimental("SKEXP0020")]
public sealed class VectorStoreBuilder
{
    private readonly Func<IServiceProvider, IVectorStore> _innerStoreFactory;

    /// <summary>The registered store factory instances.</summary>
    private List<Func<IVectorStore, IServiceProvider, IVectorStore>>? _storeFactories;

    /// <summary>Initializes a new instance of the <see cref="VectorStoreBuilder"/> class.</summary>
    /// <param name="innerStore">The inner <see cref="IVectorStore"/> that represents the underlying backend.</param>
    public VectorStoreBuilder(IVectorStore innerStore)
    {
        Verify.NotNull(innerStore);

        this._innerStoreFactory = _ => innerStore;
    }

    /// <summary>Initializes a new instance of the <see cref="VectorStoreBuilder"/> class.</summary>
    /// <param name="innerStoreFactory">A callback that produces the inner <see cref="IVectorStore"/> that represents the underlying backend.</param>
    public VectorStoreBuilder(Func<IServiceProvider, IVectorStore> innerStoreFactory)
    {
        Verify.NotNull(innerStoreFactory);

        this._innerStoreFactory = innerStoreFactory;
    }

    /// <summary>Builds an <see cref="IVectorStore"/> that represents the entire pipeline. Calls to this instance will pass through each of the pipeline stages in turn.</summary>
    /// <param name="services">
    /// The <see cref="IServiceProvider"/> that should provide services to the <see cref="IVectorStore"/> instances.
    /// If null, an empty <see cref="IServiceProvider"/> will be used.
    /// </param>
    /// <returns>An instance of <see cref="IVectorStore"/> that represents the entire pipeline.</returns>
    public IVectorStore Build(IServiceProvider? services = null)
    {
        services ??= EmptyKeyedServiceProvider.Instance;
        var vectorStore = this._innerStoreFactory(services);

        // To match intuitive expectations, apply the factories in reverse order, so that the first factory added is the outermost.
        if (this._storeFactories is not null)
        {
            for (var i = this._storeFactories.Count - 1; i >= 0; i--)
            {
                vectorStore = this._storeFactories[i](vectorStore, services);
                if (vectorStore is null)
                {
                    throw new InvalidOperationException(
                        $"The {nameof(VectorStoreBuilder)} entry at index {i} returned null. " +
                        $"Ensure that the callbacks passed to {nameof(Use)} return non-null {nameof(IVectorStore)} instances.");
                }
            }
        }

        return vectorStore;
    }

    /// <summary>Adds a factory for an intermediate vector store to the vector store pipeline.</summary>
    /// <param name="storeFactory">The store factory function.</param>
    /// <returns>The updated <see cref="VectorStoreBuilder"/> instance.</returns>
    public VectorStoreBuilder Use(Func<IVectorStore, IVectorStore> storeFactory)
    {
        Verify.NotNull(storeFactory);

        return this.Use((innerStore, _) => storeFactory(innerStore));
    }

    /// <summary>Adds a factory for an intermediate vector store to the vector store pipeline.</summary>
    /// <param name="storeFactory">The store factory function.</param>
    /// <returns>The updated <see cref="VectorStoreBuilder"/> instance.</returns>
    public VectorStoreBuilder Use(Func<IVectorStore, IServiceProvider, IVectorStore> storeFactory)
    {
        Verify.NotNull(storeFactory);

        (this._storeFactories ??= []).Add(storeFactory);
        return this;
    }
}
