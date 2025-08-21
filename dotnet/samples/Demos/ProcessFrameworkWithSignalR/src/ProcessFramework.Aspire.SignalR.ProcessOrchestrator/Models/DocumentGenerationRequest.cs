// Copyright (c) Microsoft. All rights reserved.

namespace ProcessFramework.Aspire.SignalR.ProcessOrchestrator.Models;

public class DocumentGenerationRequest
{
    public string? ProcessId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public string UserDescription { get; set; } = string.Empty;
    public bool DocumentationApproved { get; set; }
    public string? Reason { get; set; }
    public ProcessData? ProcessData { get; set; }
}

public class ProcessData
{
    public string ProcessId { get; set; } = string.Empty;
}
