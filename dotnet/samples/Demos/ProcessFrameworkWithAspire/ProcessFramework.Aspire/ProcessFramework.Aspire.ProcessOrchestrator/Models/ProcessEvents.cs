// Copyright (c) Microsoft. All rights reserved.

namespace ProcessFramework.Aspire.ProcessOrchestrator.Models;

public static class ProcessEvents
{
    public static readonly string TranslateDocument = nameof(TranslateDocument);
    public static readonly string DocumentTranslated = nameof(DocumentTranslated);
    public static readonly string SummarizeDocument = nameof(SummarizeDocument);
    public static readonly string DocumentSummarized = nameof(DocumentSummarized);
}
