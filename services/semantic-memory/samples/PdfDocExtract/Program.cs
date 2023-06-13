// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services.DataFormats.Pdf;

var text = new PdfDecoder().DocToText("file1.pdf");

Console.WriteLine(text);
