// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ProcessWithCloudEvents.Processes.Steps;

public class PublishDocumentationStep : KernelProcessStep
{
    [KernelFunction]
    public string OnPublishDocumentation(string document, bool userApproval)
    {
        string publishedDoc = $"DOCUMENT {document} is Approved";
        return publishedDoc;
    }
}
