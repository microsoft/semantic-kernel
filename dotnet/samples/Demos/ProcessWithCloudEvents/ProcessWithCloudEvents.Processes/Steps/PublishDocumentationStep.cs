// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Processes.Models;

namespace ProcessWithCloudEvents.Processes.Steps;

/// <summary>
/// Step that publishes the generated documentation
/// </summary>
public class PublishDocumentationStep : KernelProcessStep
{
    /// <summary>
    /// Function that publishes the generated documentation
    /// </summary>
    /// <param name="document">document to be published</param>
    /// <param name="userApproval">approval from the user</param>
    /// <returns><see cref="DocumentInfo"/></returns>
    [KernelFunction]
    public DocumentInfo OnPublishDocumentation(DocumentInfo document, bool userApproval)
    {
        Console.WriteLine($"Document {document.Title} has been approved by the user");
        return document;
    }
}
