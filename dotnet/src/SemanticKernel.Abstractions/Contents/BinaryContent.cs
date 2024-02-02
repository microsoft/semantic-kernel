// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides access to binary content.
/// </summary>
public sealed class BinaryContent : KernelContent
{
    private readonly Func<Task<Stream>> _streamProvider;

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class.
    /// </summary>
    /// <param name="streamProvider">The asyncronous stream provider</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public BinaryContent(
        Func<Task<Stream>> streamProvider,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this._streamProvider = streamProvider;
    }

    /// <summary>
    /// The content stream
    /// </summary>
    public async Task<Stream> GetStreamAsync() =>
        await this._streamProvider.Invoke().ConfigureAwait(false);
}
