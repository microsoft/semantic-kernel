// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Contains helpers for reading vector store model properties and their attributes.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class VectorStoreSearchResultMapping
{
    /// <summary>
    /// Convert the given <see cref="VectorSearchResults{TRecord}"/> to a <see cref="VectorlessSearchResults{TRecord}"/> instance.
    /// </summary>
    /// <typeparam name="TRecord">The type of the returned data model.</typeparam>
    /// <param name="vectorSearchResults">The <see cref="VectorSearchResults{TRecord}"/> to convert.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The converted <see cref="VectorlessSearchResults{TRecord}"/> instance.</returns>
    public static VectorlessSearchResults<TRecord> ConvertToVectorlessSearchResults<TRecord>(
        VectorSearchResults<TRecord> vectorSearchResults,
        CancellationToken cancellationToken)
    {
        var convertedItems = ConvertToRecordOnlyEnumerableAsync(vectorSearchResults.Results, cancellationToken);

        return new VectorlessSearchResults<TRecord>(convertedItems)
        {
            TotalCount = vectorSearchResults.TotalCount,
            Metadata = vectorSearchResults.Metadata,
        };
    }

    /// <summary>
    /// Convert the given list of vector search results to a list containing only the records.
    /// </summary>
    /// <typeparam name="TRecord">The type of the returned data model.</typeparam>
    /// <param name="vectorSearchResults">The vector search results to convert.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The converted records.</returns>
    private static async IAsyncEnumerable<TRecord> ConvertToRecordOnlyEnumerableAsync<TRecord>(
        IAsyncEnumerable<VectorSearchResult<TRecord>> vectorSearchResults,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await foreach (var result in vectorSearchResults.ConfigureAwait(false))
        {
            yield return result.Record;
        }
    }
}
