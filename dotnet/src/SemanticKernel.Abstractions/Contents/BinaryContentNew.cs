// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CA1056 // URI-like properties should not be strings

using System;
using System.IO;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides access to binary content.
/// </summary>
public class BinaryContentNew : KernelContent
{
    private readonly Func<Task<Stream>>? _streamProvider;
    private readonly Func<Task<ReadOnlyMemory<byte>>>? _byteArrayProvider;
    private string? _uri;
    private ReadOnlyMemory<byte>? _cachedByteArrayContent;

    /// <summary>
    /// Indicates whether the content can be read. If false content is usually is referenced by URI.
    /// </summary>
    /// <returns>True if the content can be read, false otherwise.</returns>
    public bool CanRead()
        => this._byteArrayProvider is not null
        || this._streamProvider is not null
        || this._uri?.StartsWith("data:", StringComparison.OrdinalIgnoreCase) == true;

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

        bool isDataUri = this._uri?.StartsWith("data:", StringComparison.OrdinalIgnoreCase) == true;
        if (isDataUri)
        {
            return this._uri;
        }

        // If the Uri is not a DataUri, then we need to generate it.
        await this.CacheByteArrayContentAsync(isDataUri).ConfigureAwait(false);

        this._uri = $"data:{base.MimeType};base64," + Convert.ToBase64String(this._cachedByteArrayContent!.Value.ToArray());
        return this._uri;
    }

    private async Task CacheByteArrayContentAsync(bool isDataUri)
    {
        if (this._cachedByteArrayContent is null)
        {
            // Ensure readContent is always set once a DataUri is generated.
            this._cachedByteArrayContent = isDataUri switch
            {
                true => Convert.FromBase64String(this._uri!.Substring(this._uri!.IndexOf(',') + 1)),
                _ when this._byteArrayProvider is not null => await this._byteArrayProvider().ConfigureAwait(false),
                _ when this._streamProvider is not null => await this.GetMemoryStreamFromStreamProviderAsync().ConfigureAwait(false),
                _ => throw new InvalidOperationException("No content provider available.")
            };
        }
    }

    private async Task<ReadOnlyMemory<byte>> GetMemoryStreamFromStreamProviderAsync()
    {
        using var stream = await this._streamProvider!().ConfigureAwait(false);
        using var memoryStream = new MemoryStream();
        await stream.CopyToAsync(memoryStream).ConfigureAwait(false);
        return memoryStream.ToArray();
    }

    /*
    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class.
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

        this.Uri = uri;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class.
    /// </summary>
    /// <param name="content">The binary content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public BinaryContentNew(
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
    */
}
