﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using Grpc.Core;
using Microsoft.SemanticKernel;
using Microsoft.VisualStudio.Threading;
using ProcessWithCloudEvents.Grpc.Clients;
using ProcessWithCloudEvents.Grpc.Contract;
using ProcessWithCloudEvents.Processes;
using ProcessWithCloudEvents.Processes.Models;

namespace ProcessWithCloudEvents.Grpc.LocalRuntime.Services;

/// <summary>
/// This gRPC service handles the generation of documents using/invoking a SK Process
/// </summary>
public class DocumentGenerationService : GrpcDocumentationGeneration.GrpcDocumentationGenerationBase
{
    private readonly ILogger<DocumentGenerationService> _logger;
    private readonly Kernel _kernel;

    private readonly KernelProcess _kernelProcess;
    private readonly IExternalKernelProcessMessageChannel _externalMessageChannel;
    private readonly IProcessStorageConnector _storageConnector;

    private readonly ConcurrentDictionary<string, ConcurrentBag<IServerStreamWriter<DocumentationContentRequest>>> _docReviewSubscribers;
    private readonly ConcurrentDictionary<string, ConcurrentBag<IServerStreamWriter<DocumentationContentRequest>>> _publishDocumentSubscribers;
    /// <summary>
    /// Constructor for the <see cref="DocumentGenerationService"/>
    /// </summary>
    /// <param name="logger"></param>
    /// <param name="kernel"></param>
    /// <param name="externalMessageChannel"></param>
    /// <param name="storageConnector"></param>
    public DocumentGenerationService(
        ILogger<DocumentGenerationService> logger,
        Kernel kernel,
        [FromKeyedServices("DocumentGenerationGrpcClient")] IExternalKernelProcessMessageChannel externalMessageChannel,
        IProcessStorageConnector storageConnector)
    {
        this._logger = logger;
        this._kernel = kernel;
        this._docReviewSubscribers = new();
        this._publishDocumentSubscribers = new();

        this._kernelProcess = DocumentGenerationProcess.CreateProcessBuilder().Build();

        this._externalMessageChannel = externalMessageChannel;
        this._storageConnector = storageConnector;
    }

    /// <summary>
    /// Method that receives a request to generate documentation, this will start the SK process
    /// defined in <see cref="DocumentGenerationProcess.CreateProcessBuilder"/> <br/>
    /// It will use the processId passed in the request or generate a new one if not provided
    /// </summary>
    /// <param name="request"></param>
    /// <param name="context"></param>
    /// <returns></returns>
    public override async Task<ProcessData> UserRequestFeatureDocumentation(FeatureDocumentationRequest request, ServerCallContext context)
    {
        var processId = string.IsNullOrEmpty(request.ProcessId) ? Guid.NewGuid().ToString() : request.ProcessId;

        var processContext = await this._kernelProcess.StartAsync(this._kernel, new KernelProcessEvent()
        {
            Id = DocumentGenerationProcess.DocGenerationEvents.StartDocumentGeneration,
            // The object ProductInfo is sent because this is the type the GatherProductInfoStep is expecting
            Data = new ProductInfo() { Title = request.Title, Content = request.Content, UserInput = request.UserDescription },
        }, processId, this._externalMessageChannel, this._storageConnector);

        return new ProcessData { ProcessId = processId };
    }

    /// <summary>
    /// Method that receives a request to request user review of documentation, this will send a request to the client
    /// if subscribed to the <see cref="RequestUserReviewDocumentation"/> method previously with the same process id.<br/>
    /// This method is meant to be used within the SK process from the <see cref="DocumentGenerationGrpcClient"/> implementation.
    /// </summary>
    /// <param name="request"></param>
    /// <param name="context"></param>
    /// <returns></returns>
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

    /// <summary>
    /// Method that receives request to receive user review of documentation. <br/>
    /// This is meant to be used by the external client
    /// </summary>
    /// <param name="request"></param>
    /// <param name="responseStream"></param>
    /// <param name="context"></param>
    /// <returns></returns>
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
#pragma warning disable CS8600 // Converting null literal or possible null value to non-nullable type.
            subscribers.TryTake(out responseStream);
#pragma warning restore CS8600 // Converting null literal or possible null value to non-nullable type.
        }
    }

    /// <summary>
    /// Method that receives a request to approve or reject documentation, this will send the response to the SK process.
    /// This is meant to be used by the external client.
    /// </summary>
    /// <param name="request"></param>
    /// <param name="context"></param>
    /// <returns></returns>
    public override async Task<Empty> UserReviewedDocumentation(DocumentationApprovalRequest request, ServerCallContext context)
    {
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

        var processId = request.ProcessData.ProcessId;
        var processContext = await this._kernelProcess.StartAsync(this._kernel, processEvent, processId, this._externalMessageChannel, this._storageConnector);

        return new Empty();
    }

    /// <summary>
    /// Method used to publish the generated documentation, this will send the documentation to the client
    /// if subscribed to the <see cref="ReceivePublishedDocumentation"/> method with the same process id.<br/>
    /// This method is meant to be used within the SK process from the <see cref="DocumentGenerationGrpcClient"/> implementation.
    /// </summary>
    /// <param name="request"></param>
    /// <param name="context"></param>
    /// <returns></returns>
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

    /// <summary>
    /// Method that receives request to receive published documentation from a specific process id.
    /// This is meant to be used by the external client.
    /// </summary>
    /// <param name="request"></param>
    /// <param name="responseStream"></param>
    /// <param name="context"></param>
    /// <returns></returns>
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
#pragma warning disable CS8600 // Converting null literal or possible null value to non-nullable type.
            subscribers.TryTake(out responseStream);
#pragma warning restore CS8600 // Converting null literal or possible null value to non-nullable type.
        }
    }
}
