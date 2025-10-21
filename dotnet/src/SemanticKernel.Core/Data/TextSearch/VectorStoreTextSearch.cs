// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// A Vector Store Text Search implementation that can be used to perform searches using a <see cref="VectorStoreCollection{TKey, TRecord}"/>.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VectorStoreTextSearch<[DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicProperties | DynamicallyAccessedMemberTypes.PublicMethods)] TRecord> : ITextSearch<TRecord>, ITextSearch
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>
    /// Create an instance of the <see cref="VectorStoreTextSearch{TRecord}"/> with the
    /// provided <see cref="IVectorSearchable{TRecord}"/> for performing searches and
    /// <see cref="IEmbeddingGenerator"/> for generating vectors from the text search query.
    /// </summary>
    /// <param name="vectorSearchable"><see cref="IVectorSearchable{TRecord}"/> instance used to perform the search.</param>
    /// <param name="embeddingGenerator"><see cref="IEmbeddingGenerator"/> instance used to create a vector from the text query. Only FLOAT32 vector generation is currently supported by <see cref="VectorStoreTextSearch{TRecord}"/>. If you required a different type of vector use the built in vector generation in the vector store.</param>
    /// <param name="stringMapper"><see cref="MapFromResultToString" /> instance that can map a TRecord to a <see cref="string"/></param>
    /// <param name="resultMapper"><see cref="MapFromResultToTextSearchResult" /> instance that can map a TRecord to a <see cref="TextSearchResult"/></param>
    /// <param name="options">Options used to construct an instance of <see cref="VectorStoreTextSearch{TRecord}"/></param>
    public VectorStoreTextSearch(
        IVectorSearchable<TRecord> vectorSearchable,
        IEmbeddingGenerator<string, Embedding<float>> embeddingGenerator,
        MapFromResultToString stringMapper,
        MapFromResultToTextSearchResult resultMapper,
        VectorStoreTextSearchOptions? options = null) :
        this(
            vectorSearchable,
            embeddingGenerator,
            stringMapper is null ? null : new TextSearchStringMapper(stringMapper),
            resultMapper is null ? null : new TextSearchResultMapper(resultMapper),
            options)
    {
    }

    /// <summary>
    /// Create an instance of the <see cref="VectorStoreTextSearch{TRecord}"/> with the
    /// provided <see cref="IVectorSearchable{TRecord}"/> for performing searches and
    /// <see cref="IEmbeddingGenerator"/> for generating vectors from the text search query.
    /// </summary>
    /// <param name="vectorSearchable"><see cref="IVectorSearchable{TRecord}"/> instance used to perform the search.</param>
    /// <param name="embeddingGenerator"><see cref="IEmbeddingGenerator"/> instance used to create a vector from the text query. Only FLOAT32 vector generation is currently supported by <see cref="VectorStoreTextSearch{TRecord}"/>. If you required a different type of vector use the built in vector generation in the vector store.</param>
    /// <param name="stringMapper"><see cref="ITextSearchStringMapper" /> instance that can map a TRecord to a <see cref="string"/></param>
    /// <param name="resultMapper"><see cref="ITextSearchResultMapper" /> instance that can map a TRecord to a <see cref="TextSearchResult"/></param>
    /// <param name="options">Options used to construct an instance of <see cref="VectorStoreTextSearch{TRecord}"/></param>
    public VectorStoreTextSearch(
        IVectorSearchable<TRecord> vectorSearchable,
        IEmbeddingGenerator<string, Embedding<float>> embeddingGenerator,
        ITextSearchStringMapper? stringMapper = null,
        ITextSearchResultMapper? resultMapper = null,
#pragma warning disable CS0618 // Type or member is obsolete
        VectorStoreTextSearchOptions? options = null) :
        this(
            vectorSearchable,
            embeddingGenerator.AsTextEmbeddingGenerationService(),
            stringMapper,
            resultMapper,
            options)
#pragma warning restore CS0618 // Type or member is obsolete
    {
    }

    /// <summary>
    /// Create an instance of the <see cref="VectorStoreTextSearch{TRecord}"/> with the
    /// provided <see cref="IVectorSearchable{TRecord}"/> for performing searches and
    /// <see cref="ITextEmbeddingGenerationService"/> for generating vectors from the text search query.
    /// </summary>
    /// <param name="vectorSearchable"><see cref="IVectorSearchable{TRecord}"/> instance used to perform the search.</param>
    /// <param name="textEmbeddingGeneration"><see cref="ITextEmbeddingGenerationService"/> instance used to create a vector from the text query.</param>
    /// <param name="stringMapper"><see cref="MapFromResultToString" /> instance that can map a TRecord to a <see cref="string"/></param>
    /// <param name="resultMapper"><see cref="MapFromResultToTextSearchResult" /> instance that can map a TRecord to a <see cref="TextSearchResult"/></param>
    /// <param name="options">Options used to construct an instance of <see cref="VectorStoreTextSearch{TRecord}"/></param>
    [Obsolete("Use the constructor with IEmbeddingGenerator or use the constructor without an ITextEmbeddingGenerationService and pass a vectorSearch configured to perform embedding generation with IEmbeddingGenerator")]
    public VectorStoreTextSearch(
        IVectorSearchable<TRecord> vectorSearchable,
        ITextEmbeddingGenerationService textEmbeddingGeneration,
        MapFromResultToString stringMapper,
        MapFromResultToTextSearchResult resultMapper,
        VectorStoreTextSearchOptions? options = null) :
        this(
            vectorSearchable,
            textEmbeddingGeneration,
            stringMapper is null ? null : new TextSearchStringMapper(stringMapper),
            resultMapper is null ? null : new TextSearchResultMapper(resultMapper),
            options)
    {
    }

    /// <summary>
    /// Create an instance of the <see cref="VectorStoreTextSearch{TRecord}"/> with the
    /// provided <see cref="IVectorSearchable{TRecord}"/> for performing searches and
    /// <see cref="ITextEmbeddingGenerationService"/> for generating vectors from the text search query.
    /// </summary>
    /// <param name="vectorSearchable"><see cref="IVectorSearchable{TRecord}"/> instance used to perform the search.</param>
    /// <param name="textEmbeddingGeneration"><see cref="ITextEmbeddingGenerationService"/> instance used to create a vector from the text query.</param>
    /// <param name="stringMapper"><see cref="ITextSearchStringMapper" /> instance that can map a TRecord to a <see cref="string"/></param>
    /// <param name="resultMapper"><see cref="ITextSearchResultMapper" /> instance that can map a TRecord to a <see cref="TextSearchResult"/></param>
    /// <param name="options">Options used to construct an instance of <see cref="VectorStoreTextSearch{TRecord}"/></param>
    [Obsolete("Use the constructor with IEmbeddingGenerator or use the constructor without an ITextEmbeddingGenerationService and pass a vectorSearch configured to perform embedding generation with IEmbeddingGenerator")]
    public VectorStoreTextSearch(
        IVectorSearchable<TRecord> vectorSearchable,
        ITextEmbeddingGenerationService textEmbeddingGeneration,
        ITextSearchStringMapper? stringMapper = null,
        ITextSearchResultMapper? resultMapper = null,
        VectorStoreTextSearchOptions? options = null)
    {
        Verify.NotNull(vectorSearchable);
        Verify.NotNull(textEmbeddingGeneration);

        this._vectorSearchable = vectorSearchable;
        this._textEmbeddingGeneration = textEmbeddingGeneration;
        this._propertyReader = new Lazy<TextSearchResultPropertyReader>(() => new TextSearchResultPropertyReader(typeof(TRecord)));
        this._stringMapper = stringMapper ?? this.CreateTextSearchStringMapper();
        this._resultMapper = resultMapper ?? this.CreateTextSearchResultMapper();
    }

    /// <summary>
    /// Create an instance of the <see cref="VectorStoreTextSearch{TRecord}"/> with the
    /// provided <see cref="IVectorSearchable{TRecord}"/> for performing searches and
    /// <see cref="ITextEmbeddingGenerationService"/> for generating vectors from the text search query.
    /// </summary>
    /// <param name="vectorSearchable"><see cref="IVectorSearchable{TRecord}"/> instance used to perform the text search.</param>
    /// <param name="stringMapper"><see cref="MapFromResultToString" /> instance that can map a TRecord to a <see cref="string"/></param>
    /// <param name="resultMapper"><see cref="MapFromResultToTextSearchResult" /> instance that can map a TRecord to a <see cref="TextSearchResult"/></param>
    /// <param name="options">Options used to construct an instance of <see cref="VectorStoreTextSearch{TRecord}"/></param>
    public VectorStoreTextSearch(
        IVectorSearchable<TRecord> vectorSearchable,
        MapFromResultToString stringMapper,
        MapFromResultToTextSearchResult resultMapper,
        VectorStoreTextSearchOptions? options = null) :
        this(
            vectorSearchable,
            new TextSearchStringMapper(stringMapper),
            new TextSearchResultMapper(resultMapper),
            options)
    {
    }

    /// <summary>
    /// Create an instance of the <see cref="VectorStoreTextSearch{TRecord}"/> with the
    /// provided <see cref="IVectorSearchable{TRecord}"/> for performing searches and
    /// <see cref="ITextEmbeddingGenerationService"/> for generating vectors from the text search query.
    /// </summary>
    /// <param name="vectorSearchable"><see cref="IVectorSearchable{TRecord}"/> instance used to perform the text search.</param>
    /// <param name="stringMapper"><see cref="ITextSearchStringMapper" /> instance that can map a TRecord to a <see cref="string"/></param>
    /// <param name="resultMapper"><see cref="ITextSearchResultMapper" /> instance that can map a TRecord to a <see cref="TextSearchResult"/></param>
    /// <param name="options">Options used to construct an instance of <see cref="VectorStoreTextSearch{TRecord}"/></param>
    public VectorStoreTextSearch(
        IVectorSearchable<TRecord> vectorSearchable,
        ITextSearchStringMapper? stringMapper = null,
        ITextSearchResultMapper? resultMapper = null,
        VectorStoreTextSearchOptions? options = null)
    {
        Verify.NotNull(vectorSearchable);

        this._vectorSearchable = vectorSearchable;
        this._propertyReader = new Lazy<TextSearchResultPropertyReader>(() => new TextSearchResultPropertyReader(typeof(TRecord)));
        this._stringMapper = stringMapper ?? this.CreateTextSearchStringMapper();
        this._resultMapper = resultMapper ?? this.CreateTextSearchResultMapper();
    }

    /// <inheritdoc/>
    public Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var searchResponse = this.ExecuteVectorSearchAsync(query, searchOptions, cancellationToken);

        return Task.FromResult(new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken)));
    }

    /// <inheritdoc/>
    public Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var searchResponse = this.ExecuteVectorSearchAsync(query, searchOptions, cancellationToken);

        return Task.FromResult(new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken)));
    }

    /// <inheritdoc/>
    public Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var searchResponse = this.ExecuteVectorSearchAsync(query, searchOptions, cancellationToken);

        return Task.FromResult(new KernelSearchResults<object>(this.GetResultsAsRecordAsync(searchResponse, cancellationToken)));
    }

    /// <inheritdoc/>
    [RequiresDynamicCode("LINQ filtering over generic types requires dynamic code generation for expression trees.")]
    Task<KernelSearchResults<string>> ITextSearch<TRecord>.SearchAsync(string query, TextSearchOptions<TRecord>? searchOptions, CancellationToken cancellationToken)
    {
        var searchResponse = this.ExecuteVectorSearchAsync(query, searchOptions, cancellationToken);

        return Task.FromResult(new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken)));
    }

    /// <inheritdoc/>
    [RequiresDynamicCode("LINQ filtering over generic types requires dynamic code generation for expression trees.")]
    Task<KernelSearchResults<TextSearchResult>> ITextSearch<TRecord>.GetTextSearchResultsAsync(string query, TextSearchOptions<TRecord>? searchOptions, CancellationToken cancellationToken)
    {
        var searchResponse = this.ExecuteVectorSearchAsync(query, searchOptions, cancellationToken);

        return Task.FromResult(new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken)));
    }

    /// <inheritdoc/>
    [RequiresDynamicCode("LINQ filtering over generic types requires dynamic code generation for expression trees.")]
    Task<KernelSearchResults<object>> ITextSearch<TRecord>.GetSearchResultsAsync(string query, TextSearchOptions<TRecord>? searchOptions, CancellationToken cancellationToken)
    {
        var searchResponse = this.ExecuteVectorSearchAsync(query, searchOptions, cancellationToken);

        return Task.FromResult(new KernelSearchResults<object>(this.GetResultsAsRecordAsync(searchResponse, cancellationToken)));
    }

    #region private
    [Obsolete("This property is obsolete.")]
    private readonly ITextEmbeddingGenerationService? _textEmbeddingGeneration;
    private readonly IVectorSearchable<TRecord>? _vectorSearchable;
    private readonly ITextSearchStringMapper _stringMapper;
    private readonly ITextSearchResultMapper _resultMapper;
    private readonly Lazy<TextSearchResultPropertyReader> _propertyReader;

    /// <summary>
    /// Result mapper which converts a TRecord to a <see cref="TextSearchResult"/>.
    /// </summary>
    private TextSearchResultMapper CreateTextSearchResultMapper()
    {
        return new TextSearchResultMapper(result =>
        {
            if (typeof(TRecord) != result.GetType())
            {
                throw new ArgumentException($"Expected result of type {typeof(TRecord).FullName} but got {result.GetType().FullName}.");
            }

            var value = this._propertyReader.Value.GetValue(result) ?? throw new InvalidOperationException($"Value property of {typeof(TRecord).FullName} cannot be null.");
            var name = this._propertyReader.Value.GetName(result);
            var link = this._propertyReader.Value.GetLink(result);

            return new TextSearchResult(value)
            {
                Name = name,
                Link = link,
            };
        });
    }

    /// <summary>
    /// Result mapper which converts a TRecord to a <see cref="string"/>.
    /// </summary>
    private TextSearchStringMapper CreateTextSearchStringMapper()
    {
        return new TextSearchStringMapper(result =>
        {
            if (typeof(TRecord) != result.GetType())
            {
                throw new ArgumentException($"Expected result of type {typeof(TRecord).FullName} but got {result.GetType().FullName}.");
            }

            var value = this._propertyReader.Value.GetValue(result);
            return (string?)value ?? throw new InvalidOperationException("Value property cannot be null.");
        });
    }

    /// <summary>
    /// Execute a vector search and return the results using legacy filtering for backward compatibility.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Search options with legacy TextSearchFilter.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async IAsyncEnumerable<VectorSearchResult<TRecord>> ExecuteVectorSearchAsync(string query, TextSearchOptions? searchOptions, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        searchOptions ??= new TextSearchOptions();
        var vectorSearchOptions = new VectorSearchOptions<TRecord>
        {
#pragma warning disable CS0618 // VectorSearchFilter is obsolete
            OldFilter = searchOptions.Filter?.FilterClauses is not null ? new VectorSearchFilter(searchOptions.Filter.FilterClauses) : null,
#pragma warning restore CS0618 // VectorSearchFilter is obsolete
            Skip = searchOptions.Skip,
        };

        await foreach (var result in this.ExecuteVectorSearchCoreAsync(query, vectorSearchOptions, searchOptions.Top, cancellationToken).ConfigureAwait(false))
        {
            yield return result;
        }
    }

    /// <summary>
    /// Execute a vector search and return the results using modern LINQ filtering.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Search options with LINQ filtering.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async IAsyncEnumerable<VectorSearchResult<TRecord>> ExecuteVectorSearchAsync(string query, TextSearchOptions<TRecord>? searchOptions, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        searchOptions ??= new TextSearchOptions<TRecord>();
        var vectorSearchOptions = new VectorSearchOptions<TRecord>
        {
            Filter = searchOptions.Filter, // Use modern LINQ filtering directly
            Skip = searchOptions.Skip,
        };

        await foreach (var result in this.ExecuteVectorSearchCoreAsync(query, vectorSearchOptions, searchOptions.Top, cancellationToken).ConfigureAwait(false))
        {
            yield return result;
        }
    }

    /// <summary>
    /// Core vector search execution logic.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="vectorSearchOptions">Vector search options.</param>
    /// <param name="top">Maximum number of results to return.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    private async IAsyncEnumerable<VectorSearchResult<TRecord>> ExecuteVectorSearchCoreAsync(string query, VectorSearchOptions<TRecord> vectorSearchOptions, int top, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
#pragma warning disable CS0618 // Type or member is obsolete
        if (this._textEmbeddingGeneration is not null)
        {
            var vectorizedQuery = await this._textEmbeddingGeneration!.GenerateEmbeddingAsync(query, cancellationToken: cancellationToken).ConfigureAwait(false);

            await foreach (var result in this._vectorSearchable!.SearchAsync(vectorizedQuery, top, vectorSearchOptions, cancellationToken).WithCancellation(cancellationToken).ConfigureAwait(false))
            {
                yield return result;
            }

            yield break;
        }
#pragma warning restore CS0618 // Type or member is obsolete

        await foreach (var result in this._vectorSearchable!.SearchAsync(query, top, vectorSearchOptions, cancellationToken).WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            yield return result;
        }
    }

    /// <summary>
    /// Return the search results as instances of TRecord.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<object> GetResultsAsRecordAsync(IAsyncEnumerable<VectorSearchResult<TRecord>>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null)
        {
            yield break;
        }

        await foreach (var result in searchResponse.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            if (result.Record is not null)
            {
                yield return result.Record;
                await Task.Yield();
            }
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<TextSearchResult> GetResultsAsTextSearchResultAsync(IAsyncEnumerable<VectorSearchResult<TRecord>>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null)
        {
            yield break;
        }

        await foreach (var result in searchResponse.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            if (result.Record is not null)
            {
                yield return this._resultMapper.MapFromResultToTextSearchResult(result.Record);
                await Task.Yield();
            }
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<string> GetResultsAsStringAsync(IAsyncEnumerable<VectorSearchResult<TRecord>>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null)
        {
            yield break;
        }

        await foreach (var result in searchResponse.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            if (result.Record is not null)
            {
                yield return this._stringMapper.MapFromResultToString(result.Record);
                await Task.Yield();
            }
        }
    }

    /// <summary>
    /// Converts a legacy TextSearchFilter to a modern LINQ expression for direct filtering.
    /// This eliminates the need for obsolete VectorSearchFilter conversion.
    /// </summary>
    /// <param name="filter">The legacy TextSearchFilter to convert.</param>
    /// <returns>A LINQ expression equivalent to the filter, or null if no filter is provided.</returns>
    [RequiresDynamicCode("Calls Microsoft.SemanticKernel.Data.VectorStoreTextSearch<TRecord>.CreateSingleClauseExpression(FilterClause)")]
    private static Expression<Func<TRecord, bool>>? ConvertTextSearchFilterToLinq(TextSearchFilter? filter)
    {
        if (filter?.FilterClauses == null || !filter.FilterClauses.Any())
        {
            return null;
        }

        var clauses = filter.FilterClauses.ToList();

        // Handle single clause cases first (most common and optimized)
        if (clauses.Count == 1)
        {
            return CreateSingleClauseExpression(clauses[0]);
        }

        // Handle multiple clauses with AND logic
        return CreateMultipleClauseExpression(clauses);
    }

    /// <summary>
    /// Creates a LINQ expression for a single filter clause.
    /// </summary>
    /// <param name="clause">The filter clause to convert.</param>
    /// <returns>A LINQ expression equivalent to the clause, or null if conversion is not supported.</returns>
    [RequiresDynamicCode("Calls Microsoft.SemanticKernel.Data.VectorStoreTextSearch<TRecord>.CreateAnyTagEqualToExpression(String, String)")]
    private static Expression<Func<TRecord, bool>>? CreateSingleClauseExpression(FilterClause clause)
    {
        return clause switch
        {
            EqualToFilterClause equalityClause => CreateEqualityExpression(equalityClause.FieldName, equalityClause.Value),
            AnyTagEqualToFilterClause anyTagClause => CreateAnyTagEqualToExpression(anyTagClause.FieldName, anyTagClause.Value),
            _ => null // Unsupported clause type, fallback to legacy behavior
        };
    }

    /// <summary>
    /// Creates a LINQ expression combining multiple filter clauses with AND logic.
    /// </summary>
    /// <param name="clauses">The filter clauses to combine.</param>
    /// <returns>A LINQ expression representing clause1 AND clause2 AND ... clauseN, or null if any clause cannot be converted.</returns>
    [RequiresDynamicCode("Calls Microsoft.SemanticKernel.Data.VectorStoreTextSearch<TRecord>.CreateClauseBodyExpression(FilterClause, ParameterExpression)")]
    private static Expression<Func<TRecord, bool>>? CreateMultipleClauseExpression(IList<FilterClause> clauses)
    {
        try
        {
            var parameter = Expression.Parameter(typeof(TRecord), "record");
            Expression? combinedExpression = null;

            foreach (var clause in clauses)
            {
                var clauseExpression = CreateClauseBodyExpression(clause, parameter);
                if (clauseExpression == null)
                {
                    // If any clause cannot be converted, return null for fallback
                    return null;
                }

                combinedExpression = combinedExpression == null
                    ? clauseExpression
                    : Expression.AndAlso(combinedExpression, clauseExpression);
            }

            return combinedExpression == null
                ? null
                : Expression.Lambda<Func<TRecord, bool>>(combinedExpression, parameter);
        }
        catch (ArgumentNullException)
        {
            return null;
        }
        catch (ArgumentException)
        {
            return null;
        }
        catch (InvalidOperationException)
        {
            return null;
        }
#pragma warning disable CA1031 // Intentionally catching all exceptions for graceful fallback
        catch (Exception)
        {
            return null;
        }
#pragma warning restore CA1031
    }

    /// <summary>
    /// Creates the body expression for a filter clause using a shared parameter.
    /// </summary>
    /// <param name="clause">The filter clause to convert.</param>
    /// <param name="parameter">The shared parameter expression.</param>
    /// <returns>The body expression for the clause, or null if conversion is not supported.</returns>
    [RequiresDynamicCode("Calls Microsoft.SemanticKernel.Data.VectorStoreTextSearch<TRecord>.CreateAnyTagEqualToBodyExpression(String, String, ParameterExpression)")]
    private static Expression? CreateClauseBodyExpression(FilterClause clause, ParameterExpression parameter)
    {
        return clause switch
        {
            EqualToFilterClause equalityClause => CreateEqualityBodyExpression(equalityClause.FieldName, equalityClause.Value, parameter),
            AnyTagEqualToFilterClause anyTagClause => CreateAnyTagEqualToBodyExpression(anyTagClause.FieldName, anyTagClause.Value, parameter),
            _ => null
        };
    }

    /// <summary>
    /// Creates a LINQ equality expression for a given field name and value.
    /// </summary>
    /// <param name="fieldName">The property name to compare.</param>
    /// <param name="value">The value to compare against.</param>
    /// <returns>A LINQ expression representing fieldName == value.</returns>
    private static Expression<Func<TRecord, bool>>? CreateEqualityExpression(string fieldName, object value)
    {
        try
        {
            var parameter = Expression.Parameter(typeof(TRecord), "record");
            var bodyExpression = CreateEqualityBodyExpression(fieldName, value, parameter);

            return bodyExpression == null
                ? null
                : Expression.Lambda<Func<TRecord, bool>>(bodyExpression, parameter);
        }
        catch (ArgumentNullException)
        {
            return null;
        }
        catch (ArgumentException)
        {
            return null;
        }
        catch (InvalidOperationException)
        {
            return null;
        }
#pragma warning disable CA1031 // Intentionally catching all exceptions for graceful fallback
        catch (Exception)
        {
            return null;
        }
#pragma warning restore CA1031
    }

    /// <summary>
    /// Creates the body expression for equality comparison.
    /// </summary>
    /// <param name="fieldName">The property name to compare.</param>
    /// <param name="value">The value to compare against.</param>
    /// <param name="parameter">The parameter expression.</param>
    /// <returns>The body expression for equality, or null if not supported.</returns>
    private static BinaryExpression? CreateEqualityBodyExpression(string fieldName, object value, ParameterExpression parameter)
    {
        try
        {
            // Get property: record.FieldName
            var property = typeof(TRecord).GetProperty(fieldName, BindingFlags.Public | BindingFlags.Instance);
            if (property == null)
            {
                return null;
            }

            var propertyAccess = Expression.Property(parameter, property);

            // Create constant: value
            var constant = Expression.Constant(value);

            // Create equality: record.FieldName == value
            return Expression.Equal(propertyAccess, constant);
        }
        catch (ArgumentNullException)
        {
            return null;
        }
        catch (ArgumentException)
        {
            return null;
        }
        catch (InvalidOperationException)
        {
            return null;
        }
        catch (TargetParameterCountException)
        {
            // Lambda expression parameter mismatch
            return null;
        }
        catch (MemberAccessException)
        {
            // Property access not permitted or member doesn't exist
            return null;
        }
        catch (NotSupportedException)
        {
            // Operation not supported (e.g., byref-like parameters)
            return null;
        }
#pragma warning disable CA1031 // Intentionally catching all exceptions for graceful fallback
        catch (Exception)
        {
            // Catch any other unexpected reflection or expression exceptions
            // This maintains backward compatibility rather than throwing exceptions
            return null;
        }
#pragma warning restore CA1031
    }

    /// <summary>
    /// Creates a LINQ expression for AnyTagEqualTo filtering (collection contains).
    /// </summary>
    /// <param name="fieldName">The property name (must be a collection type).</param>
    /// <param name="value">The value that the collection should contain.</param>
    /// <returns>A LINQ expression representing collection.Contains(value).</returns>
    [RequiresDynamicCode("Calls Microsoft.SemanticKernel.Data.VectorStoreTextSearch<TRecord>.CreateAnyTagEqualToBodyExpression(String, String, ParameterExpression)")]
    private static Expression<Func<TRecord, bool>>? CreateAnyTagEqualToExpression(string fieldName, string value)
    {
        try
        {
            var parameter = Expression.Parameter(typeof(TRecord), "record");
            var bodyExpression = CreateAnyTagEqualToBodyExpression(fieldName, value, parameter);

            return bodyExpression == null
                ? null
                : Expression.Lambda<Func<TRecord, bool>>(bodyExpression, parameter);
        }
        catch (ArgumentNullException)
        {
            return null;
        }
        catch (ArgumentException)
        {
            return null;
        }
        catch (InvalidOperationException)
        {
            return null;
        }
#pragma warning disable CA1031 // Intentionally catching all exceptions for graceful fallback
        catch (Exception)
        {
            return null;
        }
#pragma warning restore CA1031
    }

    /// <summary>
    /// Creates the body expression for AnyTagEqualTo comparison (collection contains).
    /// </summary>
    /// <param name="fieldName">The property name (must be a collection type).</param>
    /// <param name="value">The value that the collection should contain.</param>
    /// <param name="parameter">The parameter expression.</param>
    /// <returns>The body expression for collection contains, or null if not supported.</returns>
    [RequiresDynamicCode("Calls System.Reflection.MethodInfo.MakeGenericMethod(params Type[])")]
    [UnconditionalSuppressMessage("Trimming", "IL2075:UnrecognizedReflectionPattern", Justification = "This method uses reflection for LINQ expression building and is marked with RequiresDynamicCode to indicate AOT incompatibility.")]
    [UnconditionalSuppressMessage("Trimming", "IL2060:UnrecognizedReflectionPattern", Justification = "This method uses reflection for LINQ expression building and is marked with RequiresDynamicCode to indicate AOT incompatibility.")]
    private static MethodCallExpression? CreateAnyTagEqualToBodyExpression(string fieldName, string value, ParameterExpression parameter)
    {
        try
        {
            // Get property: record.FieldName
            var property = typeof(TRecord).GetProperty(fieldName, BindingFlags.Public | BindingFlags.Instance);
            if (property == null)
            {
                return null;
            }

            var propertyAccess = Expression.Property(parameter, property);

            // Check if property is a collection that supports Contains
            var propertyType = property.PropertyType;

            // Support ICollection<string>, List<string>, string[], IEnumerable<string>
            if (propertyType.IsGenericType)
            {
                var genericType = propertyType.GetGenericTypeDefinition();
                var itemType = propertyType.GetGenericArguments()[0];

                // Only support string collections for AnyTagEqualTo
                if (itemType == typeof(string))
                {
                    // Look for Contains method: collection.Contains(value)
#pragma warning disable IL2075 // GetMethod on property type - acceptable for reflection-based expression building
                    var containsMethod = propertyType.GetMethod("Contains", new[] { typeof(string) });
#pragma warning restore IL2075
                    if (containsMethod != null)
                    {
                        var constant = Expression.Constant(value);
                        return Expression.Call(propertyAccess, containsMethod, constant);
                    }

                    // Fallback to LINQ Contains for IEnumerable<string>
                    if (typeof(System.Collections.Generic.IEnumerable<string>).IsAssignableFrom(propertyType))
                    {
#pragma warning disable IL2060 // MakeGenericMethod with known string type - acceptable for expression building
                        var linqContainsMethod = typeof(Enumerable).GetMethods()
                            .Where(m => m.Name == "Contains" && m.GetParameters().Length == 2)
                            .FirstOrDefault()?.MakeGenericMethod(typeof(string));
#pragma warning restore IL2060

                        if (linqContainsMethod != null)
                        {
                            var constant = Expression.Constant(value);
                            return Expression.Call(linqContainsMethod, propertyAccess, constant);
                        }
                    }
                }
            }
            // Support string arrays
            else if (propertyType == typeof(string[]))
            {
#pragma warning disable IL2060 // MakeGenericMethod with known string type - acceptable for expression building
                var linqContainsMethod = typeof(Enumerable).GetMethods()
                    .Where(m => m.Name == "Contains" && m.GetParameters().Length == 2)
                    .FirstOrDefault()?.MakeGenericMethod(typeof(string));
#pragma warning restore IL2060

                if (linqContainsMethod != null)
                {
                    var constant = Expression.Constant(value);
                    return Expression.Call(linqContainsMethod, propertyAccess, constant);
                }
            }

            return null;
        }
        catch (ArgumentNullException)
        {
            return null;
        }
        catch (ArgumentException)
        {
            return null;
        }
        catch (InvalidOperationException)
        {
            return null;
        }
        catch (TargetParameterCountException)
        {
            return null;
        }
        catch (MemberAccessException)
        {
            return null;
        }
        catch (NotSupportedException)
        {
            return null;
        }
#pragma warning disable CA1031 // Intentionally catching all exceptions for graceful fallback
        catch (Exception)
        {
            return null;
        }
#pragma warning restore CA1031
    }

    #endregion
}
