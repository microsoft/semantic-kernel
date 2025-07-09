// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Processes.Models;
using ProcessWithCloudEvents.Processes.Steps;

namespace ProcessWithCloudEvents.Processes;

/// <summary>
/// Components related to the SK Process for generating documentation
/// </summary>
public static class DocumentGenerationProcess
{
    /// <summary>
    /// The key that the process will be registered with in the SK process runtime.
    /// </summary>
    public static string Key => nameof(DocumentGenerationProcess);

    /// <summary>
    /// SK Process events emitted by <see cref="DocumentGenerationProcess"/>
    /// </summary>
    public static class DocGenerationEvents
    {
        /// <summary>
        /// Event to start the document generation process
        /// </summary>
        public const string StartDocumentGeneration = nameof(StartDocumentGeneration);
        /// <summary>
        /// Event emitted when the user rejects the document
        /// </summary>
        public const string UserRejectedDocument = nameof(UserRejectedDocument);
        /// <summary>
        /// Event emitted when the user approves the document
        /// </summary>
        public const string UserApprovedDocument = nameof(UserApprovedDocument);
    }

    public static class ProcessInputEvents
    {
        public static readonly KernelProcessEventDescriptor<ProductInfo> StartDocumentGeneration = new(nameof(StartDocumentGeneration));
        public static readonly KernelProcessEventDescriptor<bool> UserApprovedDocument = new(nameof(UserApprovedDocument));
        public static readonly KernelProcessEventDescriptor<string> UserRejectedDocument = new(nameof(UserRejectedDocument));
    }

    /// <summary>
    /// SK Process topics emitted by <see cref="DocumentGenerationProcess"/>
    /// Topics are used to emit events to external systems
    /// </summary>
    public static class DocGenerationTopics
    {
        /// <summary>
        /// Request user review document generation topic
        /// </summary>
        public const string RequestUserReview = nameof(RequestUserReview);
        /// <summary>
        /// Publish documentat generated topic
        /// </summary>
        public const string PublishDocumentation = nameof(PublishDocumentation);
    }

    /// <summary>
    /// Creates a process builder for the Document Generation SK Process
    /// </summary>
    /// <param name="processName">name of the SK Process</param>
    /// <returns>instance of <see cref="ProcessBuilder"/></returns>
    public static ProcessBuilder CreateProcessBuilder(string processName = "DocumentationGeneration")
    {
        // Create the process builder 
        ProcessBuilder processBuilder = new(processName, processOptions: new() { JsonSerializerAdditionalContexts = [DocumentJsonSerializerContext.Default] });

        // Add the steps
        var infoGatheringStep = processBuilder.AddStepFromType<GatherProductInfoStep>();
        var docsGenerationStep = processBuilder.AddStepFromType<GenerateDocumentationStep>();
        var docsProofreadStep = processBuilder.AddStepFromType<ProofReadDocumentationStep>();
        var docsPublishStep = processBuilder.AddStepFromType<PublishDocumentationStep>();

        var proxyStep = processBuilder.AddProxyStep(id: processName, [DocGenerationTopics.RequestUserReview, DocGenerationTopics.PublishDocumentation]);

        // Orchestrate the external input events
        processBuilder
            .OnInputEvent(ProcessInputEvents.StartDocumentGeneration)
            .SendEventTo(new(infoGatheringStep));

        processBuilder
            .OnInputEvent(DocGenerationEvents.UserRejectedDocument)
            .SendEventTo(new(docsGenerationStep, functionName: GenerateDocumentationStep.ProcessFunctions.ApplySuggestions));

        //processBuilder
        //    .OnInputEvent(DocGenerationEvents.UserApprovedDocument)
        //    .SendEventTo(new(docsPublishStep, parameterName: "userApproval"));

        // Hooking up the rest of the process steps
        infoGatheringStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(docsGenerationStep, functionName: GenerateDocumentationStep.ProcessFunctions.GenerateDocs));

        docsGenerationStep
            .OnEvent(GenerateDocumentationStep.StepEvents.DocumentationGenerated)
            .SendEventTo(new ProcessFunctionTargetBuilder(docsProofreadStep));

        docsProofreadStep
            .OnEvent(ProofReadDocumentationStep.StepEvents.DocumentationRejected)
            .SendEventTo(new ProcessFunctionTargetBuilder(docsGenerationStep, functionName: GenerateDocumentationStep.ProcessFunctions.ApplySuggestions));

        // When the proofreader approves the documentation, send it to the 'docs' parameter of the docsPublishStep
        // Additionally, the generated document is emitted externally for user approval using the pre-configured proxyStep
        docsProofreadStep
            .OnEvent(ProofReadDocumentationStep.StepEvents.DocumentationApproved)
            .EmitExternalEvent(proxyStep, DocGenerationTopics.RequestUserReview)
            .EmitAsPublicEvent();
        //.SendEventTo(new ProcessFunctionTargetBuilder(docsPublishStep, parameterName: "document"));

        processBuilder
            .ListenFor()
            .AllOf([
                new TypedMessageSourceBuilder<DocumentInfo>(messageType: ProofReadDocumentationStep.StepEvents.DocumentationApproved, docsProofreadStep),
                new TypedMessageSourceBuilder<bool>(messageType: ProcessInputEvents.UserApprovedDocument, processBuilder),
            ])
            .SendEventTo(new ProcessStepTargetBuilder(docsPublishStep, inputMapping: (inputEvents) =>
            {
                return new() {
                    { "document", inputEvents[docsProofreadStep.GetFullEventId(ProofReadDocumentationStep.StepEvents.DocumentationApproved)] },
                    { "userApproval", inputEvents[processBuilder.GetFullEventId(ProcessInputEvents.UserApprovedDocument)] },
                };
            }));

        // When event is approved by user, it gets published externally too
        docsPublishStep
            .OnFunctionResult()
            .EmitExternalEvent(proxyStep, DocGenerationTopics.PublishDocumentation)
            .EmitAsPublicEvent();

        return processBuilder;
    }
}

[JsonSerializable(typeof(ProductInfo))]
[JsonSerializable(typeof(DocumentInfo))]
public partial class DocumentJsonSerializerContext : JsonSerializerContext;
