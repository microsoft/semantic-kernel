// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Processes.Steps;

namespace ProcessWithCloudEvents.Processes;

public static class DocumentGenerationProcess
{
    public static class DocGenerationEvents
    {
        public const string StartDocumentGeneration = nameof(StartDocumentGeneration);
        public const string UserRejectedDocument = nameof(UserRejectedDocument);
        public const string UserApprovedDocument = nameof(UserApprovedDocument);
    }

    public static class DocGenerationTopics
    {
        public const string RequestUserReview = nameof(RequestUserReview);
        public const string PublishDocumentation = nameof(PublishDocumentation);
    }

    public static ProcessBuilder CreateProcessBuilder(string processName = "DocumentationGeneration")
    {
        // Create the process builder
        ProcessBuilder processBuilder = new(processName);

        // Add the steps
        var infoGatheringStep = processBuilder.AddStepFromType<GatherProductInfoStep>();
        var docsGenerationStep = processBuilder.AddStepFromType<GenerateDocumentationStep>();
        var docsProofreadStep = processBuilder.AddStepFromType<ProofReadDocumentationStep>();
        var docsPublishStep = processBuilder.AddStepFromType<PublishDocumentationStep>();

        var proxyStep = processBuilder.AddProxyStep([DocGenerationTopics.RequestUserReview, DocGenerationTopics.PublishDocumentation]);

        // Orchestrate the external input events
        processBuilder
            .OnInputEvent(DocGenerationEvents.StartDocumentGeneration)
            .SendEventTo(new(infoGatheringStep));

        processBuilder
            .OnInputEvent(DocGenerationEvents.UserRejectedDocument)
            .SendEventTo(new(docsGenerationStep, functionName: GenerateDocumentationStep.Functions.ApplySuggestions));

        processBuilder
            .OnInputEvent(DocGenerationEvents.UserApprovedDocument)
            .SendEventTo(new(docsPublishStep, parameterName: "userApproval"));

        // Hooking up the rest of the process steps
        infoGatheringStep
            .OnFunctionResult()
            .SendEventTo(new(docsGenerationStep, functionName: GenerateDocumentationStep.Functions.GenerateDocs));

        docsGenerationStep
            .OnEvent(GenerateDocumentationStep.OutputEvents.DocumentationGenerated)
            .SendEventTo(new(docsProofreadStep));

        docsProofreadStep
            .OnEvent(ProofReadDocumentationStep.OutputEvents.DocumentationRejected)
            .SendEventTo(new(docsGenerationStep, functionName: GenerateDocumentationStep.Functions.ApplySuggestions));

        // When the proofreader approves the documentation, send it to the 'docs' parameter of the docsPublishStep
        // Additionally, the generated document is emitted externally for user approval using the pre-configured proxyStep
        docsProofreadStep
            .OnEvent(ProofReadDocumentationStep.OutputEvents.DocumentationApproved)
            .EmitExternalEvent(proxyStep, DocGenerationTopics.RequestUserReview)
            .SendEventTo(new(docsPublishStep, parameterName: "document"));

        // When event is approved by user, it gets published externally too
        docsPublishStep
            .OnFunctionResult()
            .EmitExternalEvent(proxyStep, DocGenerationTopics.PublishDocumentation);

        return processBuilder;
    }
}
