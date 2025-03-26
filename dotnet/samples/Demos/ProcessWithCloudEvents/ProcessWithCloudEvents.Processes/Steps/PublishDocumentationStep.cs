// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Processes.Models;

namespace ProcessWithCloudEvents.Processes.Steps;

public class PublishDocumentationStep : KernelProcessStep
{
    [KernelFunction]
    public DocumentInfo OnPublishDocumentation(DocumentInfo document, bool userApproval)
    {
        Console.WriteLine($"Document {document.Title} has been approved by the user");
        return document;
    }
}
