// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

#pragma warning disable CA1056 // URI-like properties should not be strings
#pragma warning disable CA1055 // URI-like parameters should not be strings
#pragma warning disable CA1054 // URI-like parameters should not be strings

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides access to binary content.
/// </summary>
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
    [JsonPropertyOrder(100), JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] // Ensuring Data Uri is serialized last for better visibility of other properties.
    public ReadOnlyMemory<byte>? Data
    {
        get => this.GetData();
        set => this.SetData(value);
    }

    /// <summary>
    /// Indicates whether the content contains binary data in either <see cref="Data"/> or <see cref="DataUri"/> properties.
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
    public BinaryContent(Uri uri)
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
        string dataUri)
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
            throw new UriFormatException("Invalid data uri. Scheme should start with \"data:\"");
        }

        // Validate the dataUri format
        var parsedDataUri = DataUriParser.Parse(dataUri);

        // Overwrite the mimetype to the DataUri.
        this.MimeType = parsedDataUri.MimeType;

        // If parameters where provided in the data uri, updates the content metadata.
        if (parsedDataUri.Parameters.Count != 0)
        {
            // According to the RFC 2397, the data uri supports custom parameters
            // This method ensures that if parameter is provided those will be added
            // to the content metadata with a "data-uri-" prefix.
            this.UpdateDataUriParametersToMetadata(parsedDataUri);
        }

        this._dataUri = dataUri;

        // Invalidate the current bytearray
        this._data = null;
    }

    private void UpdateDataUriParametersToMetadata(DataUriParser.DataUri parsedDataUri)
    {
        if (parsedDataUri.Parameters.Count == 0)
        {
            return;
        }

        var newMetadata = this.Metadata as Dictionary<string, object?>;
        if (newMetadata is null)
        {
            newMetadata = new Dictionary<string, object?>();
            if (this.Metadata is not null)
            {
                foreach (var property in this.Metadata!)
                {
                    newMetadata[property.Key] = property.Value;
                }
            }
        }

        // Overwrite any properties if already defined
        foreach (var property in parsedDataUri.Parameters)
        {
            // Set the properties from the DataUri metadata
            newMetadata[$"data-uri-{property.Key}"] = property.Value;
        }

        this.Metadata = newMetadata;
    }

    private string GetDataUriParametersFromMetadata()
    {
        var metadata = this.Metadata;
        if (metadata is null || metadata.Count == 0)
        {
            return string.Empty;
        }

        StringBuilder parameters = new();
        foreach (var property in metadata)
        {
            if (property.Key.StartsWith("data-uri-", StringComparison.OrdinalIgnoreCase))
            {
                parameters.Append($";{property.Key.AsSpan(9).ToString()}={property.Value}");
            }
        }

        return parameters.ToString();
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
            // Double check if the set MimeType matches the current dataUri.
            var parsedDataUri = DataUriParser.Parse(this._dataUri);
            if (string.Equals(parsedDataUri.MimeType, this.MimeType, StringComparison.OrdinalIgnoreCase))
            {
                return this._dataUri;
            }
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
            throw new InvalidOperationException("Can't get the data uri without a mime type defined for the content.");
        }

        // Ensure that if any data-uri-parameter defined in the metadata those will be added to the data uri.
        this._dataUri = $"data:{this.MimeType}{this.GetDataUriParametersFromMetadata()};base64," + Convert.ToBase64String(cachedByteArray.Value.ToArray());
        return this._dataUri;
    }

    private ReadOnlyMemory<byte>? GetCachedByteArrayContent()
    {
        if (this._data is null && this._dataUri is not null)
        {
            var parsedDataUri = DataUriParser.Parse(this._dataUri);
            if (string.Equals(parsedDataUri.DataFormat, "base64", StringComparison.OrdinalIgnoreCase))
            {
                this._data = Convert.FromBase64String(parsedDataUri.Data!);
            }
            else
            {
                // Defaults to UTF8 encoding if format is not provided.
                this._data = Encoding.UTF8.GetBytes(parsedDataUri.Data!);
            }
        }

        return this._data;
    }
    #endregion
}
