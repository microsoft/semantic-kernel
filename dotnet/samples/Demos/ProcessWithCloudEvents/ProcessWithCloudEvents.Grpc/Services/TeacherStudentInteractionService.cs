// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using Dapr.Actors.Client;
using Grpc.Core;
using Microsoft.SemanticKernel;
using Microsoft.VisualStudio.Threading;
using ProcessWithCloudEvents.Grpc.Contract;
using ProcessWithCloudEvents.Processes;

namespace ProcessWithCloudEvents.Grpc.Services;

/// <summary>
/// This gRPC service handles the generation of documents using/invoking a SK Process
/// </summary>
public class TeacherStudentInteractionService : GrpcTeacherStudentInteraction.GrpcTeacherStudentInteractionBase
{
    private readonly DaprKernelProcessFactory _kernelProcessFactory;
    private readonly ILogger<TeacherStudentInteractionService> _logger;
    private readonly Kernel _kernel;
    private readonly IActorProxyFactory _actorProxyFactory;
    private readonly ConcurrentDictionary<string, ConcurrentBag<IServerStreamWriter<MessageContent>>> _studentMessagesSubscribers;
    /// <summary>
    /// Constructor for the <see cref="DocumentGenerationService"/>
    /// </summary>
    /// <param name="logger"></param>
    /// <param name="kernel"></param>
    /// <param name="actorProxy"></param>
    /// <param name="kernelProcessFactory"></param>
    public TeacherStudentInteractionService(ILogger<TeacherStudentInteractionService> logger, Kernel kernel, IActorProxyFactory actorProxy, DaprKernelProcessFactory kernelProcessFactory)
    {
        this._logger = logger;
        this._kernel = kernel;
        this._actorProxyFactory = actorProxy;
        this._studentMessagesSubscribers = new();
        this._kernelProcessFactory = kernelProcessFactory;
    }

    public override async Task<ProcessDetails> StartProcess(ProcessDetails request, ServerCallContext context)
    {
        var processId = string.IsNullOrEmpty(request.ProcessId) ? Guid.NewGuid().ToString() : request.ProcessId;
        // line below is no longer needed after addition of keyed processes
        //var process = TeacherStudentProcess.CreateProcessBuilder().Build();

        var processContext = await this._kernelProcessFactory.StartAsync(TeacherStudentProcess.Key, processId, new KernelProcessEvent()
        {
            Id = TeacherStudentProcess.ProcessEvents.StartProcess,
            Data = "Give me a welcome message with a brief summary of what you can do",
        },
        this._actorProxyFactory);

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

        var processContext = await this._kernelProcessFactory.StartAsync(DocumentGenerationProcess.Key, processId, new KernelProcessEvent()
        {
            Id = TeacherStudentProcess.ProcessEvents.TeacherAskedQuestion,
            Data = request.Content,
        },
        this._actorProxyFactory);

        return request;
    }
}
