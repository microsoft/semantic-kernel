// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using Grpc.Core;
using Microsoft.SemanticKernel;
using Microsoft.VisualStudio.Threading;
using ProcessWithCloudEvents.Grpc.Contract;
using ProcessWithCloudEvents.Processes;

namespace ProcessWithCloudEvents.Grpc.LocalRuntime.Services;

/// <summary>
/// This gRPC service handles a teacher student interaction using/invoking a SK Process
/// </summary>
public class TeacherStudentInteractionService : GrpcTeacherStudentInteraction.GrpcTeacherStudentInteractionBase
{
    private readonly ILogger<TeacherStudentInteractionService> _logger;
    private readonly Kernel _kernel;
    private readonly KernelProcess _kernelProcess;

    private readonly IExternalKernelProcessMessageChannel _externalMessageChannel;
    private readonly IProcessStorageConnector _storageConnector;

    private readonly ConcurrentDictionary<string, ConcurrentBag<IServerStreamWriter<MessageContent>>> _studentMessagesSubscribers;
    /// <summary>
    /// Constructor for the <see cref="DocumentGenerationService"/>
    /// </summary>
    /// <param name="logger"></param>
    /// <param name="kernel"></param>
    /// <param name="externalMessageChannel"></param>
    /// <param name="storageConnector"></param>
    public TeacherStudentInteractionService(
        ILogger<TeacherStudentInteractionService> logger,
        Kernel kernel,
        [FromKeyedServices("TeacherStudentInteractionGrpcClient")] IExternalKernelProcessMessageChannel externalMessageChannel,
        IProcessStorageConnector storageConnector)
    {
        this._logger = logger;
        this._kernel = kernel;

        this._studentMessagesSubscribers = new();

        this._kernelProcess = TeacherStudentProcess.CreateProcessBuilder().Build();

        this._externalMessageChannel = externalMessageChannel;
        this._storageConnector = storageConnector;
    }

    public override async Task<ProcessDetails> StartProcess(ProcessDetails request, ServerCallContext context)
    {
        var processId = string.IsNullOrEmpty(request.ProcessId) ? Guid.NewGuid().ToString() : request.ProcessId;

        var processContext = await this._kernelProcess.StartAsync(this._kernel, new KernelProcessEvent()
        {
            Id = TeacherStudentProcess.ProcessEvents.StartProcess,
            Data = "Give me a welcome message with a brief summary of what you can do",
        }, processId, this._externalMessageChannel, this._storageConnector);

        return new ProcessDetails { ProcessId = processId };
    }

    public override async Task ReceiveStudentAgentResponse(ProcessDetails request, IServerStreamWriter<MessageContent> responseStream, ServerCallContext context)
    {
        var subscribers = this._studentMessagesSubscribers.GetOrAdd(request.ProcessId, []);
        subscribers.Add(responseStream);

        try
        {
            // Wait until the client disconnects  
            await context.CancellationToken.WaitHandle.ToTask();
        }
        finally
        {
            // Remove the subscriber when client disconnects  
#pragma warning disable CS8600 // Converting null literal or possible null value to non-nullable type.
            subscribers.TryTake(out responseStream);
#pragma warning restore CS8600 // Converting null literal or possible null value to non-nullable type.
        }
    }

    public override async Task<MessageContent> PublishStudentAgentResponseFromProcess(MessageContent request, ServerCallContext context)
    {
        if (this._studentMessagesSubscribers.TryGetValue(request.ProcessId, out var subscribers))
        {
            foreach (var subscriber in subscribers)
            {
                await subscriber.WriteAsync(request).ConfigureAwait(false);
            }
        }

        return request;
    }

    public override async Task<MessageContent> RequestStudentAgentResponse(MessageContent request, ServerCallContext context)
    {
        var process = TeacherStudentProcess.CreateProcessBuilder().Build();
        var processId = request.ProcessId;

        var processContext = await this._kernelProcess.StartAsync(this._kernel, new KernelProcessEvent()
        {
            Id = TeacherStudentProcess.ProcessEvents.TeacherAskedQuestion,
            Data = request.Content,
        }, processId, this._externalMessageChannel, this._storageConnector);

        return request;
    }
}
