// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

#pragma warning disable CA1056 // URI-like properties should not be strings
#pragma warning disable CA1055 // URI-like parameters should not be strings
#pragma warning disable CA1054 // URI-like parameters should not be strings

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides access to binary content.
/// </summary>
[Experimental("SKEXP0010")]
public class BinaryContent : KernelContent
{
    private string? _cachedDataUri;
    private ReadOnlyMemory<byte>? _cachedData;
    private Uri? _referencedUri;

    /// <summary>
    /// The binary content.
    /// </summary>
    [JsonIgnore, Obsolete("Use Data instead")]
    public ReadOnlyMemory<byte>? Content => Data;

    /// <summary>
    /// Gets the referenced Uri of the content.
    /// </summary>
    [JsonPropertyName("uri")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public virtual Uri? Uri
    {
        get => this.GetUri();
        set => this.SetUri(value);
    }

    /// <summary>
    /// Gets the DataUri of the content.
    /// </summary>
    [JsonIgnore]
    public virtual string? DataUri
    {
        get => this.GetDataUri();
        set => this.SetDataUri(value);
    }

    /// <summary>
    /// Gets the byte array data of the content.
    /// </summary>
    [JsonPropertyName("data")]
    [JsonPropertyOrder(100), JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] // Ensuring Data Uri is serialized last for better visibility of other properties.
    public virtual ReadOnlyMemory<byte>? Data
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
        || this._cachedDataUri is not null;

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class with no content.
    /// </summary>
    /// <remarks>
    /// Should be used only for serialization purposes.
    /// </remarks>
    [JsonConstructor]
    public BinaryContent()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class referring to an external uri.
    /// </summary>
    public BinaryContent(Uri? uri = null)
    {
        this.Uri = uri;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class for a UriData or Uri referred content.
    /// </summary>
    /// <param name="dataUri">The Uri of the content.</param>
    public BinaryContent(
        // Uri type has a ushort size limit check which inviabilizes its usage in DataUri scenarios.
        // <see href="https://github.com/dotnet/runtime/issues/96544"/>
        string? dataUri)
    {
        this.DataUri = dataUri;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryContent"/> class from a byte array.
    /// </summary>
    /// <param name="data">Byte array content</param>
    /// <param name="mimeType">The mime type of the content</param>
    public BinaryContent(
        ReadOnlyMemory<byte> data,
        string? mimeType)
    {
        Verify.NotNull(data, nameof(data));
        if (data.IsEmpty)
        {
            throw new ArgumentException("Data cannot be empty", nameof(data));
        }

        this.MimeType = mimeType;
        this.Data = data;
    }

    /// <summary>
    /// Sets the Uri of the content.
    /// </summary>
    /// <param name="uri">Target Uri</param>
    private void SetUri(Uri? uri)
    {
        if (uri?.Scheme == "data")
        {
            throw new InvalidOperationException("For DataUri contents, use DataUri property.");
        }

        this._referencedUri = uri;
    }

    /// <summary>
    /// Gets the Uri of the content.
    /// </summary>
    /// <returns>Uri of the content</returns>
    private Uri? GetUri()
        => this._referencedUri;

    /// <summary>
    /// Sets the DataUri of the content.
    /// </summary>
    /// <param name="dataUri">DataUri of the content</param>
    /// <exception cref="ArgumentException"></exception>
    private void SetDataUri(string? dataUri)
    {
        if (dataUri is null)
        {
            this._cachedDataUri = null;

            // Invalidate the current bytearray
            this._cachedData = null;
            return;
        }

        var isDataUri = dataUri!.StartsWith("data:", StringComparison.OrdinalIgnoreCase) == true;
        if (!isDataUri)
        {
            throw new ArgumentException("Invalid data uri", nameof(dataUri));
        }

        // Gets the mimetype from the DataUri and automatically sets it.
        this.MimeType = dataUri.Substring(5, dataUri.IndexOf(';') - 5);

        this._cachedDataUri = dataUri;

        // Invalidate the current bytearray
        this._cachedData = null;
    }

    /// <summary>
    /// Sets the byte array data content.
    /// </summary>
    /// <param name="data">Byte array data content</param>
    private void SetData(ReadOnlyMemory<byte>? data)
    {
        // Overriding the content will invalidate the previous dataUri
        this._cachedDataUri = null;
        this._cachedData = data;
    }

    /// <summary>
    /// Gets the byte array data content.
    /// </summary>
    /// <returns>The byte array data content</returns>
    private ReadOnlyMemory<byte>? GetData()
    {
        return this.GetCachedByteArrayContent();
    }

    /// <summary>
    /// Gets the DataUri of the content.
    /// </summary>
    /// <returns></returns>
    private string? GetDataUri()
    {
        if (!this.CanRead())
        {
            return null;
        }

        if (this._cachedDataUri is not null)
        {
            return this._cachedDataUri;
        }

        // If the Uri is not a DataUri, then we need to get from byteArray (caching if needed) to generate it.
        return this.GetCachedUriDataFromByteArray(this.GetCachedByteArrayContent());
    }

    private string? GetCachedUriDataFromByteArray(ReadOnlyMemory<byte>? cachedByteArray)
    {
        if (cachedByteArray is null)
        {
            return null;
        }

        if (this.MimeType is null)
        {
            // May consider defaulting to application/octet-stream if not provided.
            throw new InvalidOperationException("Can't get the data uri with without a mime type defined for the content.");
        }

        this._cachedDataUri = $"data:{this.MimeType};base64," + Convert.ToBase64String(cachedByteArray.Value.ToArray());
        return this._cachedDataUri;
    }

    private ReadOnlyMemory<byte>? GetCachedByteArrayContent()
    {
        if (this._cachedData is null && this._cachedDataUri is not null)
        {
            this._cachedData = Convert.FromBase64String(this._cachedDataUri!.Substring(this._cachedDataUri.IndexOf(',') + 1));
        }

        return this._cachedData;
    }
}
