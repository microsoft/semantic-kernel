// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Services.Storage.Pipeline;

public class MimeTypes
{
    public const string PlainText = "text/plain";
    public const string MarkDown = "text/plain-markdown";
    public const string MsWord = "application/msword";
    public const string Pdf = "application/pdf";
}

public interface IMimeTypeDetection
{
    public string GetFileType(string filename);
}

public class MimeTypesDetection : IMimeTypeDetection
{
    public string GetFileType(string filename)
    {
        var test = filename.ToLowerInvariant();

        if (test.EndsWith(".txt")) { return MimeTypes.PlainText; }

        if (test.EndsWith(".md")) { return MimeTypes.MarkDown; }

        if (test.EndsWith(".doc") || test.EndsWith(".docx")) { return MimeTypes.MsWord; }

        if (test.EndsWith(".pdf")) { return MimeTypes.Pdf; }

        throw new NotSupportedException($"File type not supported: {filename}");
    }
}
