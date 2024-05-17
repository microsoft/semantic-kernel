// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

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
    private string? _dataUri;
    private ReadOnlyMemory<byte>? _data;
    private Uri? _referencedUri;

    /// <summary>
    /// The binary content.
    /// </summary>
    [JsonIgnore, Obsolete("Use Data instead")]
    public ReadOnlyMemory<byte>? Content => this.Data;

    /// <summary>
    /// Gets the referenced Uri of the content.
    /// </summary>
    [JsonPropertyName("uri")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public Uri? Uri
    {
        get => this.GetUri();
        set => this.SetUri(value);
    }

    /// <summary>
    /// Gets the DataUri of the content.
    /// </summary>
    [JsonIgnore]
    public string? DataUri
    {
        get => this.GetDataUri();
        set => this.SetDataUri(value);
    }

    /// <summary>
    /// Gets the byte array data of the content.
    /// </summary>
    [JsonPropertyName("data")]
    [JsonPropertyOrder(100), JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] // Ensuring Data Uri is serialized last for better visibility of other properties.
    public ReadOnlyMemory<byte>? Data
    {
        get => this.GetData();
        set => this.SetData(value);
    }

    /// <summary>
    /// Indicates whether the content has binary data. If false content usually must be referenced by URI.
    /// </summary>
    /// <returns>True if the content has binary data, false otherwise.</returns>
    [JsonIgnore]
    public bool CanRead
        => this._data is not null
        || this._dataUri is not null;

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

    #region Private
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
            this._dataUri = null;

            // Invalidate the current bytearray
            this._data = null;
            return;
        }

        var isDataUri = dataUri!.StartsWith("data:", StringComparison.OrdinalIgnoreCase) == true;
        if (!isDataUri)
        {
            throw new ArgumentException("Invalid data uri", nameof(dataUri));
        }

        // Validate the dataUri format
        var parsedDataUri = DataUriParser.Parse(dataUri);

        // Gets the mimetype from the DataUri and automatically sets it.
        this.MimeType = parsedDataUri.MimeType;

        this._dataUri = dataUri;

        // Invalidate the current bytearray
        this._data = null;
    }

    /// <summary>
    /// Sets the byte array data content.
    /// </summary>
    /// <param name="data">Byte array data content</param>
    private void SetData(ReadOnlyMemory<byte>? data)
    {
        // Overriding the content will invalidate the previous dataUri
        this._dataUri = null;
        this._data = data;
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
        if (!this.CanRead)
        {
            return null;
        }

        if (this._dataUri is not null)
        {
            // Check if the cached dataUri has the same content type.
            var mimeType = this._dataUri.Substring(5, this._dataUri.IndexOf(';') - 5);
            return this._dataUri;
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

        this._dataUri = $"data:{this.MimeType};base64," + Convert.ToBase64String(cachedByteArray.Value.ToArray());
        return this._dataUri;
    }

    private ReadOnlyMemory<byte>? GetCachedByteArrayContent()
    {
        if (this._data is null && this._dataUri is not null)
        {
            this._data = Convert.FromBase64String(this._dataUri!.Substring(this._dataUri.IndexOf(',') + 1));
        }

        return this._data;
    }

    private bool ValidateDataUri(string dataUri)
    {
        // Check if the dataUri has a mimeType defined.
        var mimeTypeIndex = dataUri.IndexOf(';');
        if (mimeTypeIndex == -1)
        {
            return false;
        }

        // Check if the dataUri has a base64 content.
        var base64Index = dataUri.IndexOf(',');
        if (base64Index == -1)
        {
            return false;
        }

        return true;
    }
    #endregion
}
