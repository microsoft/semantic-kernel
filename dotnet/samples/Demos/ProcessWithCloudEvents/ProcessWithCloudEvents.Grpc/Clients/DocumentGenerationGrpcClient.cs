// Copyright (c) Microsoft. All rights reserved.
using Grpc.Net.Client;
using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Grpc.DocumentationGenerator;
using ProcessWithCloudEvents.Processes;

namespace ProcessWithCloudEvents.Grpc.Clients;

public class DocumentGenerationGrpcClient : IExternalKernelProcessMessageChannel
{
    private GrpcChannel? _grpcChannel;
    private GrpcDocumentationGeneration.GrpcDocumentationGenerationClient? _grpcClient;

    /// <inheritdoc/>
    public async ValueTask Initialize()
    {
        this._grpcChannel = GrpcChannel.ForAddress("http://localhost:58641");
        this._grpcClient = new GrpcDocumentationGeneration.GrpcDocumentationGenerationClient(this._grpcChannel);
    }

    /// <inheritdoc/>
    public async ValueTask Uninitialize()
    {
        if (this._grpcChannel != null)
        {
            await this._grpcChannel.ShutdownAsync();
        }
    }

    /// <inheritdoc/>
    public async Task EmitExternalEventAsync(string externalTopicEvent, KernelProcessProxyMessage eventData)
    {
        if (this._grpcClient != null)
        {
            switch (externalTopicEvent)
            {
                case DocumentGenerationProcess.DocGenerationTopics.RequestUserReview:
                    await this._grpcClient.RequestUserReviewDocumentationFromProcessAsync(new()
                    {
                        Title = "Document for user review",
                        AssistantMessage = "",
                        Content = eventData.EventData?.ToString(),
                        ProcessData = new() { ProcessId = eventData.ProcessId }
                    });

                    return;

                case DocumentGenerationProcess.DocGenerationTopics.PublishDocumentation:
                    await this._grpcClient.PublishDocumentationAsync(new()
                    {
                        ProcessData = new() { ProcessId = eventData.ProcessId }
                    });
                    return;

                default:
                    break;
            }
        }
    }
}
