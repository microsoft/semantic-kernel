// Copyright (c) Microsoft. All rights reserved.

using System.IO;

namespace Microsoft.SemanticKernel.Skills.Document;

/// <summary>
/// Interface for document connections (e.g. Microsoft Word)
/// </summary>
public interface IDocumentConnector
{
    /// <summary>
    /// Read all text from the document.
    /// </summary>
    /// <param name="stream">Document stream</param>
    /// <returns>String containing all text from the document.</returns>
    public string ReadText(Stream stream);

    /// <summary>
    /// Initialize a document from the given stream.
    /// </summary>
    /// <param name="stream">IO stream</param>
    public void Initialize(Stream stream);

    /// <summary>
    /// Append the specified text to the document.
    /// </summary>
    /// <param name="stream">Document stream</param>
    /// <param name="text">String of text to write to the document.</param>
    public void AppendText(Stream stream, string text);
}
