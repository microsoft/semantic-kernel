// Copyright (c) Microsoft. All rights reserved.
using Grpc.Net.Client;
using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Grpc.Contract;
using ProcessWithCloudEvents.Processes;

namespace ProcessWithCloudEvents.Grpc.Clients;

/// <summary>
/// Client that implements the <see cref="IExternalKernelProcessMessageChannel"/> interface used internally by the SK process
/// to emit events to external systems.<br/>
/// This implementation is an example of a gRPC client that emits events to a gRPC server
/// </summary>
public class TeacherStudentInteractionGrpcClient : IExternalKernelProcessMessageChannel
{
    private GrpcChannel? _grpcChannel;
    private GrpcTeacherStudentInteraction.GrpcTeacherStudentInteractionClient? _grpcClient;

    /// <inheritdoc/>
    public async ValueTask Initialize()
    {
        this._grpcChannel = GrpcChannel.ForAddress("http://localhost:58641");
        this._grpcClient = new GrpcTeacherStudentInteraction.GrpcTeacherStudentInteractionClient(this._grpcChannel);
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
                case TeacherStudentProcess.InteractionTopics.AgentResponseMessage:
                    var agentResponse = message.EventData.ToObject() as ChatMessageContent;
                    if (agentResponse != null)
                    {
                        await this._grpcClient.PublishStudentAgentResponseFromProcessAsync(new()
                        {
                            User = User.Student,
                            Content = agentResponse.Content,
                            ProcessId = message.ProcessId,
                        });
                    }
                    return;

                case TeacherStudentProcess.InteractionTopics.AgentErrorMessage:
                    var agentErrorResponse = message.EventData.ToObject() as string;
                    if (agentErrorResponse != null)
                    {
                        await this._grpcClient.PublishStudentAgentResponseFromProcessAsync(new()
                        {
                            User = User.Student,
                            Content = $"ERROR: {agentErrorResponse}",
                            ProcessId = message.ProcessId,
                        });
                    }
                    return;
            }
        }
    }
}
