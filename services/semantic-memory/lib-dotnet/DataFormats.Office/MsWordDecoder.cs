// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace Microsoft.SemanticKernel.Services.DataFormats.Office;

public class MsWordDecoder
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
        var wordprocessingDocument = WordprocessingDocument.Open(data, false);
        try
        {
            StringBuilder sb = new();

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

            IEnumerable<Paragraph>? paragraphs = body.Descendants<Paragraph>();
            if (paragraphs != null)
            {
                foreach (Paragraph p in paragraphs)
                {
                    sb.AppendLine(p.InnerText);
                }
            }

            return sb.ToString();
        }
        finally
        {
            wordprocessingDocument.Dispose();
        }
    }
}
