// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services.DataFormats.Office;
using Microsoft.SemanticKernel.Services.DataFormats.Pdf;

// MS Word example
Console.WriteLine("===============================");
Console.WriteLine("=== Text in mswordfile.docx ===");
Console.WriteLine("===============================");

var text = new MsWordDecoder().DocToText("mswordfile.docx");
Console.WriteLine(text);

Console.WriteLine("============================");
Console.WriteLine("Press a Enter to continue...");
Console.ReadLine();

// PDF example 1, short document
Console.WriteLine("=========================");
Console.WriteLine("=== Text in file1.pdf ===");
Console.WriteLine("=========================");

text = new PdfDecoder().DocToText("file1.pdf");
Console.WriteLine(text);

Console.WriteLine("============================");
Console.WriteLine("Press a Enter to continue...");
Console.ReadLine();

// PDF example 2, scanned book
Console.WriteLine("=========================");
Console.WriteLine("=== Text in file2.pdf ===");
Console.WriteLine("=========================");

text = new PdfDecoder().DocToText("file2.pdf");
Console.WriteLine(text);
