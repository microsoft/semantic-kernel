// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CA1056 // URI-like properties should not be strings
#pragma warning disable CA1054 // URI-like parameters should not be strings

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides access to binary content.
/// </summary>
public class BinaryContent : KernelContent
{
    private Func<Task<(Stream Stream, string? MimeType)>>? _streamProvider;
    private Func<Task<(ReadOnlyMemory<byte> ByteArray, string? MimeType)>>? _byteArrayProvider;
    private ReadOnlyMemory<byte>? _cachedByteArrayContent;
    private string? _cachedUriData;
    private Uri? _referencedUri;

    /// <summary>
    /// Gets the Uri of the content.
    /// </summary>
    public string Uri
    {
        get => this._referencedUri?.ToString()
            ?? this._cachedUriData
            ?? this.GetCachedUriDataFromByteArray(this._cachedByteArrayContent
                ?? throw new InvalidOperationException("UriData needs to be retrieved first using GetUriDataAsync."));

        set => this.SetUri(value);
    }

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
        return this.GetCachedUriDataFromByteArray(await this.GetCachedByteArrayContentAsync().ConfigureAwait(false));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class for a UriData or Uri referred content.
    /// </summary>
    /// <param name="dataUri">The Uri of the content.</param>
    /// <remarks>
    /// This constructor should be used for serialization purposes only.
    /// </remarks>
    [JsonConstructor]
    public BinaryContent(
        // Uri type has a ushort size limit check which inviabilizes its usage in DataUri scenarios.
        string dataUri)
        : base(null, null, null)
        => this.SetUri(dataUri);

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class for a UriData or Uri referred content.
    /// </summary>
    /// <param name="dataUri">The Uri of the content.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    public BinaryContent(
        // Uri type has a ushort size limit check which inviabilizes its usage in DataUri scenarios.
        string dataUri,
        object? innerContent,
        string? modelId,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
        => this.SetUri(dataUri);

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class for a Uri.
    /// </summary>
    /// <param name="referenceUri">The uri of a referenced content.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    /// <remarks>
    /// Prefer using this method for non-datauri references.
    /// </remarks>
    public BinaryContent(
        Uri referenceUri,
        object? innerContent,
        string? modelId,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : this(referenceUri.ToString(), innerContent, modelId, metadata)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class for a byte array provider.
    /// </summary>
    /// <param name="byteArrayProvider">The asynchronous byte array and mime type provider.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    /// <remarks>
    /// To be serializeable the content needs to be retrieved first.
    /// </remarks>
    public BinaryContent(
        Func<Task<(ReadOnlyMemory<byte> ByteArray, string? MimeType)>> byteArrayProvider,
        object? innerContent = null,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        Verify.NotNull(byteArrayProvider, nameof(byteArrayProvider));

        this._byteArrayProvider = byteArrayProvider;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class from a byte array.
    /// </summary>
    /// <param name="byteArray">Byte array content</param>
    /// <param name="mimeType">The mime type of the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    public BinaryContent(
        ReadOnlyMemory<byte> byteArray,
        string mimeType,
        object? innerContent = null,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        Verify.NotNullOrWhiteSpace(mimeType, nameof(mimeType));
        Verify.NotNull(byteArray, nameof(byteArray));

        this.MimeType = mimeType;
        this._cachedByteArrayContent = byteArray;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class from a stream provider.
    /// </summary>
    /// <param name="streamProvider">The asynchronous stream and mime type provider.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    /// <remarks>
    /// The <see cref="Stream"/> is accessed and immediately disposed as soon the content is cached and generated.
    /// To be serializeable the content needs to be retrieved first.
    /// </remarks>
    public BinaryContent(
        Func<Task<(Stream Stream, string? MimeType)>> streamProvider,
        object? innerContent = null,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        Verify.NotNull(streamProvider, nameof(streamProvider));

        this._streamProvider = streamProvider;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class from a stream provider.
    /// </summary>
    /// <param name="stream">The content stream.</param>
    /// <param name="mimeType">The mime type of the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    /// <remarks>
    /// The <see cref="Stream"/> is accessed and immediately disposed as soon the content is cached and generated.
    /// </remarks>
    public BinaryContent(
        Stream stream,
        string mimeType,
        object? innerContent = null,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        Verify.NotNullOrWhiteSpace(mimeType, nameof(mimeType));
        Verify.NotNull(stream, nameof(stream));

        this.MimeType = mimeType;
        this._cachedByteArrayContent = this.GetByteArrayFromStream(stream);
        stream.Dispose();
    }

    /// <summary>
    /// The content stream
    /// </summary>
    public Task<ReadOnlyMemory<byte>> GetByteArrayAsync()
        => this.GetCachedByteArrayContentAsync();

    /// <summary>
    /// Set the Uri of the content.
    /// </summary>
    /// <param name="uri">Content Uri</param>
    public void SetUri(string uri)
    {
        Verify.NotNullOrWhiteSpace(uri, nameof(uri));

        bool isDataUri = uri.StartsWith("data:", StringComparison.OrdinalIgnoreCase) == true;

        // Overriding the Uri will invalidate any provider and previously cached content.
        if (this._cachedByteArrayContent is not null)
        {
            this._cachedByteArrayContent = null;
        }

        if (this._streamProvider is not null)
        {
            this._streamProvider = null;
        }

        if (this._byteArrayProvider is not null)
        {
            this._byteArrayProvider = null;
        }

        if (!isDataUri)
        {
            this._referencedUri = new Uri(uri);
        }
        else
        {
            // Get the mime type from the data uri.
            this.MimeType = uri.Substring(5, uri.IndexOf(";", StringComparison.OrdinalIgnoreCase) - 5);
            this._cachedUriData = uri;
        }
    }

    private string GetCachedUriDataFromByteArray(ReadOnlyMemory<byte> cachedByteArray)
    {
        if (this.MimeType is null)
        {
            // May consider defaulting to application/octet-stream if not provided.
            throw new InvalidOperationException("MimeType for the content is not set.");
        }

        this._cachedUriData = $"data:{this.MimeType};base64," + Convert.ToBase64String(cachedByteArray.ToArray());
        return this._cachedUriData;
    }

    private async Task<ReadOnlyMemory<byte>> GetCachedByteArrayContentAsync()
    {
        if (!this.CanRead())
        {
            throw new NotSupportedException("Byte array content cannot be generated as the content does not support the read operation.");
        }

        if (this._cachedByteArrayContent is null)
        {
            if (this._cachedUriData is not null)
            {
                this._cachedByteArrayContent = Convert.FromBase64String(this._cachedUriData.Substring(this._cachedUriData.IndexOf(',') + 1));
            }
            else
            if (this._byteArrayProvider is not null)
            {
                (this._cachedByteArrayContent, this.MimeType) = await this._byteArrayProvider().ConfigureAwait(false);
            }
            else
            if (this._streamProvider is not null)
            {
                (this._cachedByteArrayContent, this.MimeType) = await this.GetByteArrayFromStreamProviderAsync().ConfigureAwait(false);
                return this._cachedByteArrayContent.Value;
            }
            else
            {
                throw new InvalidOperationException("No content provider available.");
            }
        }

        return this._cachedByteArrayContent.Value;
    }

    private async Task<(ReadOnlyMemory<byte> ByteArray, string? MimeType)> GetByteArrayFromStreamProviderAsync()
    {
        (var stream, string? mimeType) = await this._streamProvider!().ConfigureAwait(false);
        using (stream)
        {
            using var memoryStream = new MemoryStream();
            await stream.CopyToAsync(memoryStream).ConfigureAwait(false);
            return (memoryStream.ToArray(), mimeType);
        }
    }

    private ReadOnlyMemory<byte> GetByteArrayFromStream(Stream stream)
    {
        using var memoryStream = new MemoryStream();
        stream.CopyTo(memoryStream);
        stream.Dispose();
        return memoryStream.ToArray();
    }

    /// <inheritdoc/>
    public override string ToString()
        => this.Uri;
}
