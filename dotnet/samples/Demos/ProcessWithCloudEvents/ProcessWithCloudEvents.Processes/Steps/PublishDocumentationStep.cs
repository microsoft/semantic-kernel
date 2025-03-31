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
        if (userApproval)
        {
            // For example purposes we just write the generated docs to the console
            Console.WriteLine($"[{nameof(PublishDocumentationStep)}]:\tPublishing product documentation approved by user: \n{document.Title}\n{document.Content}");
        }
        return document;
    }
}
