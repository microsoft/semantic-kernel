// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents image content.
/// </summary>
// To be retrocompatible with the non-experimental ImageContent it needs to have a different behavior
// than the base class BinaryContent breaking the Liskov Substitution Principle (LSP).
public sealed class ImageContent : BinaryContent
{
    private string? _dataUri;

    /// <inheritdoc />
    public override Uri? Uri { get; set; }

    /// <inheritdoc />
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public override ReadOnlyMemory<byte>? Data { get; set; }

    /// <inheritdoc />
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public override string? DataUri
    {
        get => this.GetDataUri();
        set => this.SetDataUri(value);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    [JsonConstructor]
    public ImageContent()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    /// <param name="uri">The URI of image.</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public ImageContent(
        Uri uri,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(
            dataUri: null,
            uri: null,
            innerContent,
            modelId,
            metadata)
    {
        this.Uri = uri;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    /// <param name="data">The Data used as DataUri for the image.</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public ImageContent(
        ReadOnlyMemory<byte> data,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(
            data: data,
            mimeType: null,
            uri: null,
            innerContent,
            modelId,
            metadata)
    {
    }

    /// <summary>
    /// Returns the string representation of the image.
    /// In-memory images will be represented as DataUri
    /// Remote Uri images will be represented as is
    /// </summary>
    /// <remarks>
    /// When Data is provided it takes precedence over URI
    /// </remarks>
    public override string ToString()
    {
        return this.GetDataUri() ?? this.Uri?.ToString() ?? string.Empty;
    }

    private string? GetDataUri()
    {
        if (this._dataUri is not null)
        {
            return this._dataUri;
        }

        if (this.Data is null || string.IsNullOrEmpty(this.MimeType))
        {
            return null;
        }

        return $"data:{this.MimeType};base64,{Convert.ToBase64String(this.Data.Value.ToArray())}";
    }

    private void SetDataUri(string? dataUri)
    {
        if (dataUri is null)
        {
            this._dataUri = null;
            return;
        }

        var isDataUri = dataUri?.StartsWith("data:", StringComparison.OrdinalIgnoreCase) == true;
        if (!isDataUri)
        {
            throw new ArgumentException("Invalid data uri", nameof(dataUri));
        }

        this._dataUri = dataUri;

        try
        {
            this.Uri = new Uri(dataUri);
        }
        catch (UriFormatException)
        {
            // If the dataUri is too big this will fail and no Uri will be set to the property.
        }

        // Do not reset the Data and MimeTypes like Binary would do to keep consistency
        // with the Uri and Data individualities.
    }
}
