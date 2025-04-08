// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Abstract base class for storing and retrieving text based memories.
/// </summary>
public abstract class TextMemoryStore
{
    /// <summary>
    /// Retrieves a memory asynchronously by its document name.
    /// </summary>
    /// <param name="documentName">The name of the document to retrieve the memory for.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the memory text if found, otherwise null.</returns>
    public abstract Task<string?> GetMemoryAsync(string documentName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Searches for memories that are similar to the given text asynchronously.
    /// </summary>
    /// <param name="query">The text to search for similar memories.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous enumerable of similar memory texts.</returns>
    public abstract IAsyncEnumerable<string> SimilaritySearch(string query, CancellationToken cancellationToken = default);

    /// <summary>
    /// Saves a memory asynchronously with the specified document name.
    /// </summary>
    /// <param name="documentName">The name of the document to save the memory to.</param>
    /// <param name="memoryText">The memory text to save.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous save operation.</returns>
    public abstract Task SaveMemoryAsync(string documentName, string memoryText, CancellationToken cancellationToken = default);

    /// <summary>
    /// Saves a memory asynchronously with no document name.
    /// </summary>
    /// <param name="memoryText">The memory text to save.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous save operation.</returns>
    public abstract Task SaveMemoryAsync(string memoryText, CancellationToken cancellationToken = default);
}
