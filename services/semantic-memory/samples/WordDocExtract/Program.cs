// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services.DataFormats.Office;

var text = new MsWordDecoder().DocToText("file.docx");

Console.WriteLine(text);
