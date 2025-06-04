// Copyright (c) Microsoft. All rights reserved.
using Grpc.Net.Client;
using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Grpc.DocumentationGenerator;
using ProcessWithCloudEvents.Processes;
using ProcessWithCloudEvents.Processes.Models;

namespace ProcessWithCloudEvents.Grpc.Clients;

/// <summary>
/// Client that implements the <see cref="IExternalKernelProcessMessageChannel"/> interface used internally by the SK process
/// to emit events to external systems.<br/>
/// This implementation is an example of a gRPC client that emits events to a gRPC server
/// </summary>
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
    public async Task EmitExternalEventAsync(string externalTopicEvent, KernelProcessProxyMessage message)
    {
        if (this._grpcClient != null && message.EventData != null)
        {
            switch (externalTopicEvent)
            {
                case DocumentGenerationProcess.DocGenerationTopics.RequestUserReview:
                    var requestDocument = message.EventData.ToObject() as DocumentInfo;
                    if (requestDocument != null)
                    {
                        await this._grpcClient.RequestUserReviewDocumentationFromProcessAsync(new()
                        {
                            Title = requestDocument.Title,
                            AssistantMessage = "Document ready for user revision. Approve or reject document",
                            Content = requestDocument.Content,
                            ProcessData = new() { ProcessId = message.ProcessId }
                        });
                    }
                    return;

                case DocumentGenerationProcess.DocGenerationTopics.PublishDocumentation:
                    var publishedDocument = message.EventData.ToObject() as DocumentInfo;
                    if (publishedDocument != null)
                    {
                        await this._grpcClient.PublishDocumentationAsync(new()
                        {
                            Title = publishedDocument.Title,
                            AssistantMessage = "Published Document Ready",
                            Content = publishedDocument.Content,
                            ProcessData = new() { ProcessId = message.ProcessId }
                        });
                    }
                    return;
            }
        }
    }
}
