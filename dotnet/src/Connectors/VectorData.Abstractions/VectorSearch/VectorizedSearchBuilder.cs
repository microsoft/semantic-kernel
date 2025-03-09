// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.VectorData;

/// <summary>A builder for creating pipelines of <see cref="IVectorizedSearch{TRecord}"/>.</summary>
[Experimental("SKEXP0020")]
public sealed class VectorizedSearchBuilder<TRecord>
{
    private readonly Func<IServiceProvider, IVectorizedSearch<TRecord>> _innerSearchFactory;

    /// <summary>The registered search factory instances.</summary>
    private List<Func<IVectorizedSearch<TRecord>, IServiceProvider, IVectorizedSearch<TRecord>>>? _searchFactories;

    /// <summary>Initializes a new instance of the <see cref="VectorizedSearchBuilder{TRecord}"/> class.</summary>
    /// <param name="innerSearch">The inner <see cref="IVectorizedSearch{TRecord}"/> that represents the underlying backend.</param>
    public VectorizedSearchBuilder(IVectorizedSearch<TRecord> innerSearch)
    {
        Verify.NotNull(innerSearch);

        this._innerSearchFactory = _ => innerSearch;
    }

    /// <summary>Initializes a new instance of the <see cref="VectorizedSearchBuilder{TRecord}"/> class.</summary>
    /// <param name="innerSearchFactory">A callback that produces the inner <see cref="IVectorizedSearch{TRecord}"/> that represents the underlying backend.</param>
    public VectorizedSearchBuilder(Func<IServiceProvider, IVectorizedSearch<TRecord>> innerSearchFactory)
    {
        Verify.NotNull(innerSearchFactory);

        this._innerSearchFactory = innerSearchFactory;
    }

    /// <summary>Builds an <see cref="IVectorizedSearch{TRecord}"/> that represents the entire pipeline. Calls to this instance will pass through each of the pipeline stages in turn.</summary>
    /// <param name="services">
    /// The <see cref="IServiceProvider"/> that should provide services to the <see cref="IVectorizedSearch{TRecord}"/> instances.
    /// If null, an empty <see cref="IServiceProvider"/> will be used.
    /// </param>
    /// <returns>An instance of <see cref="IVectorizedSearch{TRecord}"/> that represents the entire pipeline.</returns>
    public IVectorizedSearch<TRecord> Build(IServiceProvider? services = null)
    {
        services ??= EmptyKeyedServiceProvider.Instance;
        var search = this._innerSearchFactory(services);

        // To match intuitive expectations, apply the factories in reverse order, so that the first factory added is the outermost.
        if (this._searchFactories is not null)
        {
            for (var i = this._searchFactories.Count - 1; i >= 0; i--)
            {
                search = this._searchFactories[i](search, services);
                if (search is null)
                {
                    throw new InvalidOperationException(
                        $"The {nameof(VectorizedSearchBuilder<TRecord>)} entry at index {i} returned null. " +
                        $"Ensure that the callbacks passed to {nameof(Use)} return non-null {nameof(IVectorizedSearch<TRecord>)} instances.");
                }
            }
        }

        return search;
    }

    /// <summary>Adds a factory for an intermediate vectorized search to the pipeline.</summary>
    /// <param name="searchFactory">The search factory function.</param>
    /// <returns>The updated <see cref="VectorizedSearchBuilder{TRecord}"/> instance.</returns>
    public VectorizedSearchBuilder<TRecord> Use(Func<IVectorizedSearch<TRecord>, IVectorizedSearch<TRecord>> searchFactory)
    {
        Verify.NotNull(searchFactory);

        return this.Use((innerSearch, _) => searchFactory(innerSearch));
    }

    /// <summary>Adds a factory for an intermediate vectorized search to the pipeline.</summary>
    /// <param name="searchFactory">The search factory function.</param>
    /// <returns>The updated <see cref="VectorizedSearchBuilder{TRecord}"/> instance.</returns>
    public VectorizedSearchBuilder<TRecord> Use(Func<IVectorizedSearch<TRecord>, IServiceProvider, IVectorizedSearch<TRecord>> searchFactory)
    {
        Verify.NotNull(searchFactory);

        (this._searchFactories ??= []).Add(searchFactory);
        return this;
    }
}
