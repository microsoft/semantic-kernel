// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides access to binary content.
/// </summary>
[Experimental("SKEXP0015")]
public class BinaryContent : KernelContent
{
    private readonly Func<Task<Stream>>? _streamProvider;

    /// <summary>
    /// The binary content.
    /// </summary>
    public ReadOnlyMemory<byte>? Content { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class.
    /// </summary>
    [JsonConstructor]
    public BinaryContent()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class.
    /// </summary>
    /// <param name="content">The binary content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public BinaryContent(
        ReadOnlyMemory<byte> content,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        Verify.NotNull(content, nameof(content));

        this.Content = content;
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
        if (this._streamProvider is not null)
        {
            return await this._streamProvider.Invoke().ConfigureAwait(false);
        }

        if (this.Content is not null)
        {
            return new MemoryStream(this.Content.Value.ToArray());
        }

        throw new KernelException("Null content");
    }

    /// <summary>
    /// The content stream
    /// </summary>
    public async Task<ReadOnlyMemory<byte>> GetContentAsync()
    {
        if (this._streamProvider is not null)
        {
            using var stream = await this._streamProvider.Invoke().ConfigureAwait(false);

            using var memoryStream = new MemoryStream();

            await stream.CopyToAsync(memoryStream).ConfigureAwait(false);

            return memoryStream.ToArray();
        }

        if (this.Content is not null)
        {
            return this.Content.Value;
        }

        throw new KernelException("Null content");
    }
}
