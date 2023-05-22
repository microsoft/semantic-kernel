// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace Microsoft.SemanticKernel.Skills.Document.OpenXml.Extensions;

/// <summary>
/// Extension methods for DocumentFormat.OpenXml.Packaging.WordprocessingDocument
/// Note: the "Wordprocessing" vs "WordProcessing" typo is in the 3P class, we follow the original naming.
/// </summary>
internal static class WordprocessingDocumentEx
{
    internal static void Initialize(this WordprocessingDocument wordprocessingDocument)
    {
        // Add a main document part.
        MainDocumentPart mainPart = wordprocessingDocument.AddMainDocumentPart();

        // Create the document structure.
        mainPart.Document = new DocumentFormat.OpenXml.Wordprocessing.Document();
        mainPart.Document.AppendChild(new Body());
    }

    internal static string ReadText(this WordprocessingDocument wordprocessingDocument)
    {
        StringBuilder sb = new();

        var mainPart = wordprocessingDocument.MainDocumentPart;
        if (mainPart is null)
        {
            throw new InvalidOperationException("The main document part is missing.");
        }

        var body = mainPart.Document.Body;
        if (body is null)
        {
            throw new InvalidOperationException("The document body is missing.");
        }

        var paras = body.Descendants<Paragraph>();
        if (paras != null)
        {
            foreach (Paragraph para in paras)
            {
                sb.AppendLine(para.InnerText);
            }
        }

        return sb.ToString();
    }

    internal static void AppendText(this WordprocessingDocument wordprocessingDocument, string text)
    {
        if (text is null)
        {
            throw new ArgumentNullException(nameof(text));
        }

        MainDocumentPart? mainPart = wordprocessingDocument.MainDocumentPart;
        if (mainPart is null)
        {
            throw new InvalidOperationException("The main document part is missing.");
        }

        Body? body = mainPart.Document.Body;
        if (body is null)
        {
            throw new InvalidOperationException("The document body is missing.");
        }

        Paragraph para = body.AppendChild(new Paragraph());
        Run run = para.AppendChild(new Run());
        run.AppendChild(new DocumentFormat.OpenXml.Wordprocessing.Text(text));
    }
}
