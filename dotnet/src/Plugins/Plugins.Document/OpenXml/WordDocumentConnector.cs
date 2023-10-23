// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using Microsoft.SemanticKernel.Plugins.Document.OpenXml.Extensions;

namespace Microsoft.SemanticKernel.Plugins.Document.OpenXml;

/// <summary>
/// Connector for Microsoft Word (.docx) files
/// </summary>
public class WordDocumentConnector : IDocumentConnector
{
    /// <summary>
    /// Read all text from the document.
    /// </summary>
    /// <param name="stream">Document stream</param>
    /// <returns>String containing all text from the document.</returns>
    /// <exception cref="System.ArgumentNullException"></exception>
    /// <exception cref="System.InvalidOperationException"></exception>
    /// <exception cref="IOException"></exception>
    /// <exception cref="OpenXmlPackageException"></exception>
    public string ReadText(Stream stream)
    {
        using WordprocessingDocument wordprocessingDocument = WordprocessingDocument.Open(stream, false);
        return wordprocessingDocument.ReadText();
    }

    /// <summary>
    /// Initialize a document from the given stream.
    /// </summary>
    /// <param name="stream">IO stream</param>
    /// <exception cref="System.ArgumentNullException"></exception>
    /// <exception cref="IOException"></exception>
    /// <exception cref="OpenXmlPackageException"></exception>
    public void Initialize(Stream stream)
    {
        using (WordprocessingDocument wordprocessingDocument = WordprocessingDocument.Create(stream, WordprocessingDocumentType.Document))
        {
            wordprocessingDocument.Initialize();
        }

        // This is a workaround for a bug with the OpenXML SDK [TODO: add bug number]
        using (WordprocessingDocument wordprocessingDocument = WordprocessingDocument.Open(stream, false)) { }
    }

    /// <summary>
    /// Append the specified text to the document. This requires read-write permissions.
    /// </summary>
    /// <param name="stream">Document stream</param>
    /// <param name="text">String of text to write to the document.</param>
    /// <exception cref="System.ArgumentNullException"></exception>
    /// <exception cref="System.InvalidOperationException"></exception>
    /// <exception cref="IOException"></exception>
    /// <exception cref="OpenXmlPackageException"></exception>
    public void AppendText(Stream stream, string text)
    {
        using (WordprocessingDocument wordprocessingDocument = WordprocessingDocument.Open(stream, true))
        {
            wordprocessingDocument.AppendText(text);
        }

        // This is a workaround for a bug with the OpenXML SDK [TODO: add bug number]
        using (WordprocessingDocument wordprocessingDocument = WordprocessingDocument.Open(stream, false)) { }
    }
}
