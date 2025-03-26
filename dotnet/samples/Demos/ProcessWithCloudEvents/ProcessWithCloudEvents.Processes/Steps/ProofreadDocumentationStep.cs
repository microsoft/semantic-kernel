// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Processes.Models;

namespace ProcessWithCloudEvents.Processes.Steps;

/// <summary>
/// Step that determines generated document readiness
/// </summary>
public class ProofReadDocumentationStep : KernelProcessStep
{
    /// <summary>
    /// SK Process Events emitted by <see cref="ProofReadDocumentationStep"/>
    /// </summary>
    public static class OutputEvents
    {
        /// <summary>
        /// Document has errors and needs to be revised event
        /// </summary>
        public const string DocumentationRejected = nameof(DocumentationRejected);
        /// <summary>
        /// Document looks ok and can be processed by the next step
        /// </summary>
        public const string DocumentationApproved = nameof(DocumentationApproved);
    }

    /// <summary>
    /// Determines whether the document is needs a revision or is ready to be processed by the next step
    /// </summary>
    /// <param name="context">instance of <see cref="KernelProcessStepContext"/></param>
    /// <param name="document">document content that is verified</param>
    /// <returns></returns>
    [KernelFunction]
    public async Task OnProofReadDocumentAsync(KernelProcessStepContext context, DocumentInfo document)
    {
        if (document.Title.StartsWith("Generated", System.StringComparison.InvariantCulture))
        {
            // Simulating document had errors and needs corrections

            await context.EmitEventAsync(new()
            {
                Id = OutputEvents.DocumentationRejected,
                // This event is getting piped to the GenerateDocumentationStep.ApplySuggestionsAsync step which expects a string with suggestions for the document
                Data = "The document needs a revision",
            });
        }
        else
        {
            // Document has been revised
            // Events that are getting piped to steps that will be resumed, like PublishDocumentationStep.OnPublishDocumentation
            // require events to be marked as public so they are persisted and restored correctly
            await context.EmitEventAsync(OutputEvents.DocumentationApproved, document, KernelProcessEventVisibility.Public);
        }
    }
}
