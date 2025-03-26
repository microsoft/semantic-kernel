// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Processes.Models;

namespace ProcessWithCloudEvents.Processes.Steps;

public class ProofReadDocumentationStep : KernelProcessStep
{
    public static class OutputEvents
    {
        public const string DocumentationRejected = nameof(DocumentationRejected);
        public const string DocumentationApproved = nameof(DocumentationApproved);
    }

    [KernelFunction]
    public async Task OnProofReadDocumentAsync(KernelProcessStepContext context, DocumentInfo document)
    {
        if (document.Title.StartsWith("Generated", System.StringComparison.InvariantCulture))
        {
            // Simulating document had errors and needs corrections
            await context.EmitEventAsync(OutputEvents.DocumentationRejected, document, KernelProcessEventVisibility.Public);
        }
        else
        {
            // Document has been revised
            await context.EmitEventAsync(OutputEvents.DocumentationApproved, document, KernelProcessEventVisibility.Public);
        }
    }
}
