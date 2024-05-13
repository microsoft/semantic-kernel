// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CA1056 // URI-like properties should not be strings

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides access to binary content.
/// </summary>
public class BinaryContentNew : KernelContent
{
    private readonly Func<Task<Stream>>? _streamProvider;
    private readonly Func<Task<ReadOnlyMemory<byte>>>? _byteArrayProvider;
    private ReadOnlyMemory<byte>? _cachedByteArrayContent;
    private string? _cachedUriData;
    private readonly Uri? _referencedUri;

    /// <summary>
    /// Gets the Uri of the content.
    /// </summary>
    public string Uri =>
        this._referencedUri?.ToString()
        ?? this._cachedUriData
        ?? throw new InvalidOperationException("UriData needs to be retrieved first using GetUriDataAsync.");

    /// <summary>
    /// Indicates whether the content can be read. If false content usually must be referenced by URI.
    /// </summary>
    /// <returns>True if the content can be read, false otherwise.</returns>
    public bool CanRead()
        => this._cachedByteArrayContent is not null
        || this._cachedUriData is not null
        || this._byteArrayProvider is not null
        || this._streamProvider is not null;

    /// <summary>
    /// Gets the Uri information from the content
    /// </summary>
    /// <remarks>
    /// When the content is a uri reference, this will not return a UriData.
    /// </remarks>
    /// <returns></returns>
    /// <exception cref="InvalidOperationException"></exception>
    public async Task<string?> GetUriDataAsync()
    {
        if (!this.CanRead())
        {
            throw new NotSupportedException("UriData cannot be generated as the content does not support the read operation.");
        }

        if (this._cachedUriData is not null)
        {
            return this._cachedUriData;
        }

        // If the Uri is not a DataUri, then we need to get from byteArray (caching if needed) to generate it.
        return this.CacheUriDataFromByteArray(await this.CacheByteArrayContentAsync().ConfigureAwait(false));
    }

    private string CacheUriDataFromByteArray(ReadOnlyMemory<byte> cachedByteArray)
    {
        if (base.MimeType is null)
        {
            throw new InvalidOperationException("MimeType for the content is not set.");
        }

        this._cachedUriData = $"data:{base.MimeType};base64," + Convert.ToBase64String(cachedByteArray.ToArray());
        return this._cachedUriData;
    }

    private async Task<ReadOnlyMemory<byte>> CacheByteArrayContentAsync()
    {
        if (this._cachedByteArrayContent is null)
        {
            if (this._cachedUriData is not null)
            {
                this._cachedByteArrayContent = Convert.FromBase64String(this._cachedUriData.Substring(this._cachedUriData.IndexOf(',') + 1));
            }
            else
            if (this._byteArrayProvider is not null)
            {
                this._cachedByteArrayContent = await this._byteArrayProvider().ConfigureAwait(false);
            }
            else
            if (this._streamProvider is not null)
            {
                this._cachedByteArrayContent = await this.GetMemoryStreamFromStreamProviderAsync().ConfigureAwait(false);
                return this._cachedByteArrayContent.Value;
            }
            else
            {
                throw new InvalidOperationException("No content provider available.");
            }
        }

        return this._cachedByteArrayContent.Value;
    }

    private async Task<ReadOnlyMemory<byte>> GetMemoryStreamFromStreamProviderAsync()
    {
        using var stream = await this._streamProvider!().ConfigureAwait(false);
        using var memoryStream = new MemoryStream();
        await stream.CopyToAsync(memoryStream).ConfigureAwait(false);
        return memoryStream.ToArray();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class for a UriData or Uri referred content.
    /// </summary>
    [JsonConstructor]
    public BinaryContentNew(
#pragma warning disable CA1054 // URI-like parameters should not be strings
        // Uri type has a ushort size limit check which inviabilizes its usage Data Uri scenarios.
        string uri,
#pragma warning restore CA1054 // URI-like parameters should not be strings
        string? modelId,
        object? innerContent,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        Verify.NotNullOrWhiteSpace(uri, nameof(uri));

        bool isDataUri = uri.StartsWith("data:", StringComparison.OrdinalIgnoreCase) == true;

        if (!isDataUri)
        {
            this._referencedUri = new Uri(uri);
        }
        else
        {
            this._cachedUriData = uri;
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class.
    /// </summary>
    /// <param name="byteArrayProvider">The asynchronous stream provider.</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public BinaryContentNew(
        Func<Task<ReadOnlyMemory<byte>>> byteArrayProvider,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        Verify.NotNull(byteArrayProvider, nameof(byteArrayProvider));

        this._byteArrayProvider = byteArrayProvider;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class from a byte array content.
    /// </summary>
    /// <param name="byteArray">Byte array content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public BinaryContentNew(
        ReadOnlyMemory<byte> byteArray,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : this(() => Task.FromResult(byteArray), modelId, innerContent, metadata)
    {
        Verify.NotNull(byteArray, nameof(byteArray));
    }

    /*
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
    */
}
