// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using Dapr.Actors.Client;
using Grpc.Core;
using Microsoft.SemanticKernel;
using Microsoft.VisualStudio.Threading;
using ProcessWithCloudEvents.Grpc.DocumentationGenerator;
using ProcessWithCloudEvents.Processes;
using ProcessWithCloudEvents.Processes.Models;

namespace ProcessWithCloudEvents.Grpc.Services;

public class DocumentGenerationService : GrpcDocumentationGeneration.GrpcDocumentationGenerationBase
{
    private readonly ILogger<DocumentGenerationService> _logger;
    private readonly Kernel _kernel;
    private readonly IActorProxyFactory _actorProxyFactory;
    private readonly ConcurrentDictionary<string, ConcurrentBag<IServerStreamWriter<DocumentationContentRequest>>> _docReviewSubscribers;
    private readonly ConcurrentDictionary<string, ConcurrentBag<IServerStreamWriter<DocumentationContentRequest>>> _publishDocumentSubscribers;
    public DocumentGenerationService(ILogger<DocumentGenerationService> logger, Kernel kernel, IActorProxyFactory actorProxy)
    {
        this._logger = logger;
        this._kernel = kernel;
        this._actorProxyFactory = actorProxy;
        this._docReviewSubscribers = new();
        this._publishDocumentSubscribers = new();
    }

    public override async Task<ProcessData> UserRequestFeatureDocumentation(FeatureDocumentationRequest request, ServerCallContext context)
    {

        var processId = string.IsNullOrEmpty(request.ProcessId) ? Guid.NewGuid().ToString() : request.ProcessId;
        var process = DocumentGenerationProcess.CreateProcessBuilder().Build();

        var processContext = await process.StartAsync(new KernelProcessEvent()
        {
            Id = DocumentGenerationProcess.DocGenerationEvents.StartDocumentGeneration,
            // The object ProductInfo is sent because this is the type the GatherProductInfoStep is expecting
            Data = new ProductInfo() { Title = request.Title, Content = request.Content, UserInput = request.UserDescription },
        },
        processId,
        this._actorProxyFactory);

        return new ProcessData { ProcessId = processId };
    }

    public override async Task<Empty> RequestUserReviewDocumentationFromProcess(DocumentationContentRequest request, ServerCallContext context)
    {
        if (this._docReviewSubscribers.TryGetValue(request.ProcessData.ProcessId, out var subscribers))
        {
            foreach (var subscriber in subscribers)
            {
                await subscriber.WriteAsync(request).ConfigureAwait(false);
            }
        }

        return new Empty();
    }

    public override async Task RequestUserReviewDocumentation(ProcessData request, IServerStreamWriter<DocumentationContentRequest> responseStream, ServerCallContext context)
    {
        var subscribers = this._docReviewSubscribers.GetOrAdd(request.ProcessId, []);
        subscribers.Add(responseStream);

        try
        {
            // Wait until the client disconnects  
            await context.CancellationToken.WaitHandle.ToTask();
        }
        finally
        {
            // Remove the subscriber when client disconnects  
            subscribers.TryTake(out responseStream);
        }
    }

    public override async Task<Empty> UserReviewedDocumentation(DocumentationApprovalRequest request, ServerCallContext context)
    {
        var process = DocumentGenerationProcess.CreateProcessBuilder().Build();

        KernelProcessEvent processEvent;
        if (request.DocumentationApproved)
        {
            processEvent = new()
            {
                Id = DocumentGenerationProcess.DocGenerationEvents.UserApprovedDocument,
                Data = true,
            };
        }
        else
        {
            processEvent = new()
            {
                Id = DocumentGenerationProcess.DocGenerationEvents.UserRejectedDocument,
                Data = request.Reason,
            };
        }

        var processContext = await process.StartAsync(processEvent, request.ProcessData.ProcessId);

        return new Empty();
    }

    public override async Task<Empty> PublishDocumentation(DocumentationContentRequest request, ServerCallContext context)
    {
        if (this._publishDocumentSubscribers.TryGetValue(request.ProcessData.ProcessId, out var subscribers))
        {
            foreach (var subscriber in subscribers)
            {
                await subscriber.WriteAsync(request).ConfigureAwait(false);
            }
        }

        return new Empty();
    }

    public override async Task ReceivePublishedDocumentation(ProcessData request, IServerStreamWriter<DocumentationContentRequest> responseStream, ServerCallContext context)
    {
        var subscribers = this._publishDocumentSubscribers.GetOrAdd(request.ProcessId, []);
        subscribers.Add(responseStream);

        try
        {
            // Wait until the client disconnects  
            await context.CancellationToken.WaitHandle.ToTask();
        }
        finally
        {
            // Remove the subscriber when client disconnects  
            subscribers.TryTake(out responseStream);
        }
    }
}
