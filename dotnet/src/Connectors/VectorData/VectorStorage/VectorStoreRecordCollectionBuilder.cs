// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.VectorData;

/// <summary>A builder for creating pipelines of <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</summary>
[Experimental("SKEXP0020")]
public sealed class VectorStoreRecordCollectionBuilder<TKey, TRecord> where TKey : notnull
{
    private readonly Func<IServiceProvider, IVectorStoreRecordCollection<TKey, TRecord>> _innerCollectionFactory;

    /// <summary>The registered collection factory instances.</summary>
    private List<Func<IVectorStoreRecordCollection<TKey, TRecord>, IServiceProvider, IVectorStoreRecordCollection<TKey, TRecord>>>? _collectionFactories;

    /// <summary>Initializes a new instance of the <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/> class.</summary>
    /// <param name="innerCollection">The inner <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> that represents the underlying backend.</param>
    public VectorStoreRecordCollectionBuilder(IVectorStoreRecordCollection<TKey, TRecord> innerCollection)
    {
        Verify.NotNull(innerCollection);

        this._innerCollectionFactory = _ => innerCollection;
    }

    /// <summary>Initializes a new instance of the <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/> class.</summary>
    /// <param name="innerCollectionFactory">A callback that produces the inner <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> that represents the underlying backend.</param>
    public VectorStoreRecordCollectionBuilder(Func<IServiceProvider, IVectorStoreRecordCollection<TKey, TRecord>> innerCollectionFactory)
    {
        Verify.NotNull(innerCollectionFactory);

        this._innerCollectionFactory = innerCollectionFactory;
    }

    /// <summary>Builds an <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> that represents the entire pipeline. Calls to this instance will pass through each of the pipeline stages in turn.</summary>
    /// <param name="services">
    /// The <see cref="IServiceProvider"/> that should provide services to the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> instances.
    /// If null, an empty <see cref="IServiceProvider"/> will be used.
    /// </param>
    /// <returns>An instance of <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> that represents the entire pipeline.</returns>
    public IVectorStoreRecordCollection<TKey, TRecord> Build(IServiceProvider? services = null)
    {
        services ??= EmptyKeyedServiceProvider.Instance;
        var collection = this._innerCollectionFactory(services);

        // To match intuitive expectations, apply the factories in reverse order, so that the first factory added is the outermost.
        if (this._collectionFactories is not null)
        {
            for (var i = this._collectionFactories.Count - 1; i >= 0; i--)
            {
                collection = this._collectionFactories[i](collection, services);
                if (collection is null)
                {
                    throw new InvalidOperationException(
                        $"The {nameof(VectorStoreRecordCollectionBuilder<TKey, TRecord>)} entry at index {i} returned null. " +
                        $"Ensure that the callbacks passed to {nameof(Use)} return non-null {nameof(IVectorStoreRecordCollection<TKey, TRecord>)} instances.");
                }
            }
        }

        return collection;
    }

    /// <summary>Adds a factory for an intermediate vector store record collection to the pipeline.</summary>
    /// <param name="collectionFactory">The collection factory function.</param>
    /// <returns>The updated <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/> instance.</returns>
    public VectorStoreRecordCollectionBuilder<TKey, TRecord> Use(Func<IVectorStoreRecordCollection<TKey, TRecord>, IVectorStoreRecordCollection<TKey, TRecord>> collectionFactory)
    {
        Verify.NotNull(collectionFactory);

        return this.Use((innerCollection, _) => collectionFactory(innerCollection));
    }

    /// <summary>Adds a factory for an intermediate vector store record collection to the pipeline.</summary>
    /// <param name="collectionFactory">The collection factory function.</param>
    /// <returns>The updated <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/> instance.</returns>
    public VectorStoreRecordCollectionBuilder<TKey, TRecord> Use(Func<IVectorStoreRecordCollection<TKey, TRecord>, IServiceProvider, IVectorStoreRecordCollection<TKey, TRecord>> collectionFactory)
    {
        Verify.NotNull(collectionFactory);

        (this._collectionFactories ??= []).Add(collectionFactory);
        return this;
    }
}
