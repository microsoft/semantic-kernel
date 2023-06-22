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
    public class Document
    {
        /// <summary>
        /// Name of the uploaded document.
        /// </summary>
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// Size of the uploaded document in bytes.
        /// </summary>
        [JsonPropertyName("size")]
        public string Size { get; set; } = string.Empty;

        /// <summary>
        /// Status of the uploaded document.
        /// If true, the document is successfully uploaded. False otherwise.
        /// </summary>
        [JsonPropertyName("status")]
        public bool Status { get; set; } = false;
    }

    /// <summary>
    /// List of documents contained in the message.
    /// </summary>
    [JsonPropertyName("documents")]
    public List<Document> Documents { get; set; } = new List<Document>();

    /// <summary>
    /// Add a document to the list of documents.
    /// </summary>
    /// <param name="name">Name of the uploaded document</param>
    /// <param name="size">Size of the uploaded document in bytes</param>
    /// <param name="status">Status of the uploaded document</param>
    public void AddDocument(string name, string size, bool status)
    {
        Documents.Add(new Document
        {
            Name = name,
            Size = size,
            Status = status,
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
        if (Documents.Count == 0)
        {
            return string.Empty;
        }

        var formattedStrings = Documents
            .FindAll(document => document.Status)
            .Select(document => $"[Name: {document.Name}, Size: {document.Size}]");

        if (formattedStrings.Count() == 1)
        {
            return $"Uploaded a file {formattedStrings.First()}.";
        }

        return $"Uploaded files: {string.Join(", ", formattedStrings)}.";
    }

    /// <summary>
    /// Serialize the object to a formatted string that only
    /// contains file names separated by comma.
    /// </summary>
    /// <returns>A formatted string</returns>
    public string ToFormattedStringFileNamesOnly()
    {
        if (Documents.Count == 0)
        {
            return string.Empty;
        }

        var formattedStrings = Documents
            .FindAll(document => document.Status)
            .Select(document => $"{document.Name}");

        if (formattedStrings.Count() == 1)
        {
            return $"{formattedStrings.First()}";
        }

        return $"{string.Join(", ", formattedStrings)}";
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
