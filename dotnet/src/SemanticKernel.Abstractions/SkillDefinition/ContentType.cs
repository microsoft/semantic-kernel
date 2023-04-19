// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Represents a content type for HTTP requests and responses, such as application/json or text/plain.
/// </summary>
public struct ContentType
{
    // Predefined content types for common formats
    public static readonly ContentType Json = new("application/json");
    public static readonly ContentType Text = new("text/plain");
    public static readonly ContentType Csv = new("text/csv");
    public static readonly ContentType Html = new("text/html");
    public static readonly ContentType Xml = new("application/xml");
    public static readonly ContentType Jpeg = new("image/jpeg");
    public static readonly ContentType Png = new("image/png");
    public static readonly ContentType Zip = new("application/zip");
    public static readonly ContentType Pdf = new("application/pdf");

    private string _contentType;

    /// <summary>
    /// Creates a new content type with the given string.
    /// This allows specifying custom or non-standard content types as needed.
    /// </summary>
    /// <param name="contentType">The content type string, such as "text/plain"</param>
    public ContentType(string contentType)
    {
        this._contentType = contentType;
    }

    /// <summary>
    /// Returns the content type string, such as "text/plain".
    /// </summary>
    /// <returns>The content type string</returns>
    public override string ToString()
    {
        return this._contentType;
    }
}
