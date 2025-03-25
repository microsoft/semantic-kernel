// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ProcessWithCloudEvents.Processes.Steps;

public class ProofReadDocumentationStep : KernelProcessStep
{
    public static class OutputEvents
    {
        public const string DocumentationRejected = nameof(DocumentationRejected);
        public const string DocumentationApproved = nameof(DocumentationApproved);
    }

    [KernelFunction]
    public async Task OnProofReadDocumentAsync(KernelProcessStepContext context, string document)
    {
        if (document.StartsWith("Generated", System.StringComparison.InvariantCulture))
        {
            // Simulating document had errors and needs user input
            await context.EmitEventAsync(OutputEvents.DocumentationApproved, document, KernelProcessEventVisibility.Public);
        }
        else
        {
            // User provided suggestions
            await context.EmitEventAsync(OutputEvents.DocumentationApproved, document, KernelProcessEventVisibility.Public);
        }
    }
}
