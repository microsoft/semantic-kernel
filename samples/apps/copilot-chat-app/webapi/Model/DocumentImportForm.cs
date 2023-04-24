// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Model;

/// <summary>
/// Form for importing a document from a POST Http request.
/// </summary>
public class DocumentImportForm
{
    /// <summary>
    /// Scope of the document. This determines the collection name in the document memory.
    /// </summary>
    public enum DocumentScopes
    {
        Global,
        User,
    }

    /// <summary>
    /// The file to import.
    /// </summary>
    public IFormFile? FormFile { get; set; }

    /// <summary>
    /// Scope of the document. This determines the collection name in the document memory.
    /// </summary>
    public DocumentScopes DocumentScope { get; set; } = DocumentScopes.Global;

    /// <summary>
    /// The ID of the user who owns the document. This is used to create a unique collection name for the user.
    /// If the user ID is not specified or empty, the documents will be stored in a global collection.
    /// If the document scope is set to global, this value is ignored.
    /// </summary>
    public string UserId { get; set; } = string.Empty;
}
