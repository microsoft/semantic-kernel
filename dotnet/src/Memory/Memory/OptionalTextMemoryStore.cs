// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Agents.Memory;

/// <summary>
/// Helper class to get a <see cref="TextMemoryStore"/> from the DI container if a name is provided
/// and if the memory store is registered.
/// Class implements no-op methods if no name is provided or the store is not registered.
/// </summary>
internal sealed class OptionalTextMemoryStore : TextMemoryStore
{
    private readonly TextMemoryStore? _textMemoryStore;

    /// <summary>
    /// Initializes a new instance of the <see cref="OptionalTextMemoryStore"/> class.
    /// </summary>
    /// <param name="kernel">The kernel to try and get the named store from.</param>
    /// <param name="storeName">The name of the store to get from the DI container.</param>
    public OptionalTextMemoryStore(Kernel kernel, string? storeName)
    {
        if (storeName is not null)
        {
            this._textMemoryStore = kernel.Services.GetKeyedService<TextMemoryStore>(storeName);
        }
    }

    /// <inheritdoc/>
    public override Task<string?> GetMemoryAsync(string documentName, CancellationToken cancellationToken = default)
    {
        if (this._textMemoryStore is not null)
        {
            return this._textMemoryStore.GetMemoryAsync(documentName, cancellationToken);
        }

        return Task.FromResult<string?>(null);
    }

    /// <inheritdoc/>
    public override Task SaveMemoryAsync(string documentName, string memoryText, CancellationToken cancellationToken = default)
    {
        if (this._textMemoryStore is not null)
        {
            return this._textMemoryStore.SaveMemoryAsync(documentName, memoryText, cancellationToken);
        }

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public override Task SaveMemoryAsync(string memoryText, CancellationToken cancellationToken = default)
    {
        if (this._textMemoryStore is not null)
        {
            return this._textMemoryStore.SaveMemoryAsync(memoryText, cancellationToken);
        }

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public override IAsyncEnumerable<string> SimilaritySearch(string query, CancellationToken cancellationToken = default)
    {
        if (this._textMemoryStore is not null)
        {
            return this._textMemoryStore.SimilaritySearch(query, cancellationToken);
        }

        return AsyncEnumerable.Empty<string>();
    }
}
