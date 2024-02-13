// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides access to binary content.
/// </summary>
public class BinaryContent : KernelContent
{
    private readonly Func<Task<Stream>>? _streamProvider;
    private readonly BinaryData? _content;

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class.
    /// </summary>
    /// <param name="content">The binary content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public BinaryContent(
        BinaryData content,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        Verify.NotNull(content, nameof(content));

        this._content = content;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class.
    /// </summary>
    /// <param name="streamProvider">The asynchronous stream provider.</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    /// <remarks>
    /// The <see cref="Stream"/> is accessed and disposed as part of either the
    /// the <see cref="GetStreamAsync"/> or <see cref="GetContentAsync"/>
    /// accessor methods.
    /// </remarks>
    public BinaryContent(
        Func<Task<Stream>> streamProvider,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        Verify.NotNull(streamProvider, nameof(streamProvider));

        this._streamProvider = streamProvider;
    }

    /// <summary>
    /// Access the content stream.
    /// </summary>
    /// <remarks>
    /// Caller responsible for disposal.
    /// </remarks>
    public async Task<Stream> GetStreamAsync()
    {
        if (this._streamProvider != null)
        {
            return await this._streamProvider.Invoke().ConfigureAwait(false);
        }

        if (this._content != null)
        {
            return this._content.ToStream();
        }

        throw new KernelException("Null content");
    }

    /// <summary>
    /// The content stream
    /// </summary>
    public async Task<BinaryData> GetContentAsync()
    {
        if (this._streamProvider != null)
        {
            using var stream = await this._streamProvider.Invoke().ConfigureAwait(false);
            return await BinaryData.FromStreamAsync(stream).ConfigureAwait(false);
        }

        if (this._content != null)
        {
            return this._content;
        }

        throw new KernelException("Null content");
    }
}
