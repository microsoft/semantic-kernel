// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides access to binary content.
/// </summary>
public class BinaryContent : KernelContent
{
    private string? _cachedUriData;
    private ReadOnlyMemory<byte>? _cachedData;

    /// <summary>
    /// Gets the referenced Uri of the content.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public Uri? Uri { get; set; }

    /// <summary>
    /// Gets the DataUri of the content.
    /// </summary>
    [JsonPropertyOrder(100), JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] // Ensuring Data Uri is serialized last for better visibility of other properties.
    public string? DataUri
    {
        get => this.GetDataUri();
        set => this.SetDataUri(value);
    }

    /// <summary>
    /// Gets the byte array data of the content.
    /// </summary>
    [JsonIgnore]
    public ReadOnlyMemory<byte>? Data
    {
        get => this.GetData();
        set => this.SetData(value);
    }

    /// <summary>
    /// Indicates whether the content can be read. If false content usually must be referenced by URI.
    /// </summary>
    /// <returns>True if the content can be read, false otherwise.</returns>
    public bool CanRead()
        => this._cachedData is not null
        || this._cachedUriData is not null;

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class for a UriData or Uri referred content.
    /// </summary>
    /// <param name="dataUri">The Uri of the content.</param>
    /// <param name="mimeType">The mime type of the content</param>
    /// <param name="uri">The uri reference of the content.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    [JsonConstructor]
    public BinaryContent(
        // Uri type has a ushort size limit check which inviabilizes its usage in DataUri scenarios.
        string? dataUri = null,
        string? mimeType = null,
        Uri? uri = null,
        object? innerContent = null,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Uri = uri;
        this.DataUri = dataUri;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class from a byte array.
    /// </summary>
    /// <param name="data">Byte array content</param>
    /// <param name="mimeType">The mime type of the content</param>
    /// <param name="uri">The uri reference of the content.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    public BinaryContent(
        ReadOnlyMemory<byte> data,
        string? mimeType,
        Uri? uri = null,
        object? innerContent = null,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        Verify.NotNullOrWhiteSpace(mimeType, nameof(mimeType));
        Verify.NotNull(data, nameof(data));

        this.MimeType = mimeType;
        this.Data = data;
    }

    private void SetDataUri(string? dataUri)
    {
        if (dataUri is null)
        {
            this._cachedUriData = null;

            // Invalidate the current bytearray
            this._cachedData = null;
            return;
        }

        var isDataUri = dataUri!.StartsWith("data:", StringComparison.OrdinalIgnoreCase) == true;
        if (!isDataUri)
        {
            throw new ArgumentException("Invalid data uri", nameof(dataUri));
        }

        this._cachedUriData = dataUri;

        // Invalidate the current bytearray
        this._cachedData = null;
    }

    private void SetData(ReadOnlyMemory<byte>? byteArray)
    {
        // Overriding the content will invalidate the previous dataUri
        this._cachedUriData = null;
        this._cachedData = byteArray;
    }

    private ReadOnlyMemory<byte>? GetData()
    {
        if (!this.CanRead())
        {
            return null;
        }

        return this._cachedData;
    }

    private string? GetDataUri()
    {
        if (!this.CanRead())
        {
            return null;
        }

        if (this._cachedUriData is not null)
        {
            return this._cachedUriData;
        }

        // If the Uri is not a DataUri, then we need to get from byteArray (caching if needed) to generate it.
        return this.GetCachedUriDataFromByteArray(this.GetCachedByteArrayContent());
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

    private ReadOnlyMemory<byte> GetCachedByteArrayContent()
    {
        if (!this.CanRead())
        {
            throw new NotSupportedException("Byte array content cannot be generated as the content does not support the read operation.");
        }

        if (this._cachedData is null)
        {
            this._cachedData = Convert.FromBase64String(this._cachedUriData!.Substring(this._cachedUriData.IndexOf(',') + 1));
        }

        return this._cachedData!.Value;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return JsonSerializer.Serialize(this);
    }
}
