// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services.Storage.ContentStorage;
using Microsoft.SemanticKernel.Services.Storage.Queue;

namespace Microsoft.SemanticKernel.Services.Storage.Pipeline;

public class DistributedPipelineOrchestrator : BaseOrchestrator
{
    private readonly QueueClientFactory _queueClientFactory;

    private readonly Dictionary<string, IQueue> _queues = new(StringComparer.InvariantCultureIgnoreCase);

    public DistributedPipelineOrchestrator(
        IContentStorage contentStorage,
        IMimeTypeDetection mimeTypeDetection,
        QueueClientFactory queueClientFactory,
        ILogger<DistributedPipelineOrchestrator> log)
        : base(contentStorage, mimeTypeDetection, log)
    {
        this._queueClientFactory = queueClientFactory;
    }

    ///<inheritdoc />
    public override async Task AttachHandlerAsync(
        IPipelineStepHandler handler,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(handler.StepName))
        {
            throw new ArgumentNullException(nameof(handler.StepName), "The step name is empty");
        }

        if (handler == null)
        {
            throw new ArgumentNullException(nameof(handler), "The handler is NULL");
        }

        if (this._queues.ContainsKey(handler.StepName))
        {
            throw new ArgumentException($"There is already a handler for step '{handler.StepName}'");
        }

        // Create a new queue client and start listening for messages
        this._queues[handler.StepName] = this._queueClientFactory.Build();
        this._queues[handler.StepName].OnDequeue(async msg =>
        {
            var pipeline = JsonSerializer.Deserialize<DataPipeline>(msg);

            if (pipeline == null)
            {
                this.Log.LogError("Pipeline deserialization failed, queue {0}`", handler.StepName);
                // Note: returning False, the message is put back in the queue and processed again, eventually this will be moved to the poison queue if available
                return false;
            }

            // This should never occur unless there's a bug
            var currentStepName = pipeline.RemainingSteps.First();
            if (currentStepName != handler.StepName)
            {
                this.Log.LogError("Pipeline state is inconsistent. Queue `{0}` should not contain a pipeline at step `{1}`", handler.StepName, currentStepName);
                // Note: returning False, the message is put back in the queue and processed again, eventually this will be moved to the poison queue if available
                return false;
            }

            return await this.RunPipelineStepAsync(pipeline, handler, this.CancellationTokenSource.Token).ConfigureAwait(false);
        });
        await this._queues[handler.StepName].ConnectToQueueAsync(handler.StepName, QueueOptions.PubSub, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    ///<inheritdoc />
    public override async Task RunPipelineAsync(
        DataPipeline pipeline,
        CancellationToken cancellationToken = default)
    {
        // Files must be uploaded before starting any other task
        await this.UploadFilesAsync(pipeline, cancellationToken).ConfigureAwait(false);

        // In case the pipeline has no steps
        if (pipeline.Complete)
        {
            this.Log.LogInformation("Pipeline {0} complete", pipeline.Id);
            return;
        }

        await this.MoveForwardAsync(pipeline, cancellationToken).ConfigureAwait(false);
    }

    private async Task<bool> RunPipelineStepAsync(
        DataPipeline pipeline,
        IPipelineStepHandler handler,
        CancellationToken cancellationToken)
    {
        // Sync state on disk with state in the queue
        await this.UpdatePipelineStatusAsync(pipeline, cancellationToken, ignoreExceptions: false).ConfigureAwait(false);

        // In case the pipeline has no steps
        if (pipeline.Complete)
        {
            this.Log.LogInformation("Pipeline {0} complete", pipeline.Id);
            // Note: returning True, the message is removed from the queue
            return true;
        }

        string currentStepName = pipeline.RemainingSteps.First();

        // Execute the business logic - exceptions are automatically handled by IQueue
        (bool success, DataPipeline updatedPipeline) = await handler.InvokeAsync(pipeline, cancellationToken).ConfigureAwait(false);
        if (success)
        {
            pipeline = updatedPipeline;
            this.Log.LogInformation("Handler {0} processed pipeline {1} successfully", currentStepName, pipeline.Id);
            pipeline.MoveToNextStep();
            await this.MoveForwardAsync(pipeline, cancellationToken).ConfigureAwait(false);
        }
        else
        {
            this.Log.LogError("Handler {0} failed to process pipeline {1}", currentStepName, pipeline.Id);
        }

        // Note: returning True, the message is removed from the queue
        // Note: returning False, the message is put back in the queue and processed again
        return success;
    }

    private async Task MoveForwardAsync(DataPipeline pipeline, CancellationToken cancellationToken = default)
    {
        // Note: the pipeline state is persisted in two places:
        // * source of truth: in the queue (see the message enqueued)
        // * async copy: in the container together with files - this can be out of sync and is synchronized on dequeue

        // string nextStepName = pipeline.MoveToNextStep();
        string nextStepName = pipeline.RemainingSteps.First();
        this.Log.LogInformation("Enqueueing pipeline '{0}' step '{1}'", pipeline.Id, nextStepName);

        using IQueue queue = this._queueClientFactory.Build();
        await queue.ConnectToQueueAsync(nextStepName, QueueOptions.PublishOnly, cancellationToken).ConfigureAwait(false);
        await queue.EnqueueAsync(ToJson(pipeline), cancellationToken).ConfigureAwait(false);

        // Try to save the pipeline status
        await this.UpdatePipelineStatusAsync(pipeline, cancellationToken, ignoreExceptions: true).ConfigureAwait(false);
    }
}
