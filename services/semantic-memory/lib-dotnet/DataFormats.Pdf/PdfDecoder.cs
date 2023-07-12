// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text;
using UglyToad.PdfPig;
using UglyToad.PdfPig.DocumentLayoutAnalysis.TextExtractor;

namespace Microsoft.SemanticKernel.Services.DataFormats.Pdf;

public class PdfDecoder
{
    public string DocToText(string filename)
    {
        return this.DocToText(File.OpenRead(filename));
    }

    public string DocToText(BinaryData data)
    {
        return this.DocToText(data.ToStream());
    }

    public string DocToText(Stream data)
    {
        StringBuilder sb = new();
        using var pdfDocument = PdfDocument.Open(data);
        foreach (var page in pdfDocument.GetPages())
        {
            var text = ContentOrderTextExtractor.GetText(page);
            sb.Append(text);
        }

        return sb.ToString();
    }
}
