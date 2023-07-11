// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace SemanticKernel.Service.CopilotChat.Models;

/// <summary>
/// Value of `Content` for a `ChatMessage` of type `ChatMessageType.Document`.
/// </summary>
public class DocumentMessageContent
{
    /// <summary>
    /// List of documents contained in the message.
    /// </summary>
    [JsonPropertyName("documents")]
    public IEnumerable<DocumentData> Documents { get; private set; } = Enumerable.Empty<DocumentData>();

    /// <summary>
    /// Add a document to the list of documents.
    /// </summary>
    /// <param name="name">Name of the uploaded document</param>
    /// <param name="size">Size of the uploaded document in bytes</param>
    /// <param name="isUploaded">Status of the uploaded document</param>
    public void AddDocument(string name, string size, bool isUploaded)
    {
        this.Documents = this.Documents.Append(new DocumentData
        {
            Name = name,
            Size = size,
            IsUploaded = isUploaded,
        });
    }

    /// <summary>
    /// Serialize the object to a JSON string.
    /// </summary>
    /// <returns>A serialized JSON string</returns>
    public override string ToString()
    {
        return JsonSerializer.Serialize(this);
    }

    /// <summary>
    /// Serialize the object to a formatted string.
    /// Only successful uploads will be included in the formatted string.
    /// </summary>
    /// <returns>A formatted string</returns>
    public string ToFormattedString()
    {
        if (!this.Documents.Any())
        {
            return string.Empty;
        }

        var formattedStrings = this.Documents
            .Where(document => document.IsUploaded)
            .Select(document => $"[Name: {document.Name}, Size: {document.Size}]").ToList();

        if (formattedStrings.Count == 1)
        {
            return $"Uploaded a document {formattedStrings.First()}.";
        }

        return $"Uploaded documents: {string.Join(", ", formattedStrings)}.";
    }

    /// <summary>
    /// Serialize the object to a formatted string that only
    /// contains document names separated by comma.
    /// </summary>
    /// <returns>A formatted string</returns>
    public string ToFormattedStringNamesOnly()
    {
        if (!this.Documents.Any())
        {
            return string.Empty;
        }

        var formattedStrings = this.Documents
            .Where(document => document.IsUploaded)
            .Select(document => document.Name).ToList();

        if (formattedStrings.Count == 1)
        {
            return formattedStrings.First();
        }

        return string.Join(", ", formattedStrings);
    }

    /// <summary>
    /// Deserialize a JSON string to a DocumentMessageContent object.
    /// </summary>
    /// <param name="json">A JSON string</param>
    /// <returns>A DocumentMessageContent object</returns>
    public static DocumentMessageContent? FromString(string json)
    {
        return JsonSerializer.Deserialize<DocumentMessageContent>(json);
    }
}
