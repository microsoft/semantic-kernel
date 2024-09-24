// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Process;
internal sealed class LocalProcess : LocalStep
{
    private readonly List<KernelProcessStepInfo> _stepsInfos;
    private readonly List<LocalStep> _steps;
    private readonly KernelProcess _process;
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of the <see cref="LocalProcess"/> class.
    /// </summary>
    /// <param name="process">The <see cref="KernelProcess"/> instance.</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    /// <param name="parentProcessId">Optional. The Id of the parent process if one exists, otherwise null.</param>
    /// <param name="loggerFactory">Optional. A <see cref="ILoggerFactory"/>.</param>
    public LocalProcess(KernelProcess process, Kernel kernel, string? parentProcessId = null, ILoggerFactory? loggerFactory = null)
        : base(process.State.Name!, process.State.Id ?? Guid.NewGuid().ToString("n"), kernel, parentProcessId, loggerFactory)
    {
        Verify.NotNull(process);
        Verify.NotNull(process.Steps);
        Verify.NotNull(kernel);

        this._stepsInfos = new List<KernelProcessStepInfo>(process.Steps);
        this._steps = [];
        this._kernel = kernel;
        this._process = process;
    }

    public async Task ExecuteAsync(Kernel? kernel = null, KernelProcessEvent? initialEvent = null, int maxSupersteps = 100)
    {
        Kernel localKernel = kernel ?? this._kernel;
        CancellationTokenSource cancelSource = new();
        Queue<LocalMessage> messageChannel = new();

        this._outputEdges = this._process.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList());

        // Initialize the steps within this process
        foreach (var step in this._stepsInfos)
        {
            // The current step should already have a name.
            Verify.NotNull(step.State?.Name);

            LocalStep? localStep = null;

            if (step is KernelProcess kernelStep)
            {
                // The process will only have an Id if its already been executed.
                if (string.IsNullOrWhiteSpace(kernelStep.State.Id))
                {
                    kernelStep = kernelStep with { State = kernelStep.State with { Id = Guid.NewGuid().ToString() } };
                }

                var process = new LocalProcess(
                    process: kernelStep,
                    kernel: localKernel,
                    parentProcessId: this.Id,
                    loggerFactory: this.LoggerFactory);

                localStep = process;
            }
            else
            {
                // The current step should already have an Id.
                Verify.NotNull(step.State?.Id);

                localStep = new LocalStep(
                    name: step.State.Name,
                    id: step.State.Id,
                    kernel: localKernel,
                    parentProcessId: this.Id,
                    loggerFactory: this.LoggerFactory);
            }

            await localStep.InitializeAsync(step).ConfigureAwait(false);
            this._steps.Add(localStep);
        }

        if (initialEvent is not null)
        {
            if (this._outputEdges!.TryGetValue(initialEvent.Id!, out List<KernelProcessEdge>? edges) && edges is not null)
            {
                foreach (var edge in edges)
                {
                    Dictionary<string, object?> parameterValue = new();
                    if (!string.IsNullOrWhiteSpace(edge.OutputTarget.ParameterName))
                    {
                        parameterValue.Add(edge.OutputTarget.ParameterName!, initialEvent.Data);
                    }

                    LocalMessage newMessage = new(edge.SourceStepId, edge.OutputTarget.StepId, edge.OutputTarget.FunctionName, parameterValue);
                    messageChannel.Enqueue(newMessage);
                }
            }
        }

        try
        {
            // Run the Pregel algorithm until there are no more messages being sent.
            LocalStep? finalStep = null;
            for (int superstep = 0; superstep < maxSupersteps; superstep++)
            {
                // Get all of the messages that have been sent to the steps within the process and queue them up for processing.
                foreach (var step in this._steps)
                {
                    this.EnqueueStepMessagesAsync(step, kernel, messageChannel);
                }

                // Complete the writing side, indicating no more messages in this superstep.
                var messagesToProcess = messageChannel.ToList();
                messageChannel.Clear();

                if (messagesToProcess.Count == 0)
                {
                    return;
                }

                List<Task> messageTasks = [];
                foreach (var message in messagesToProcess)
                {
                    // Check for end condition
                    if (message.DestinationId.Equals("END", StringComparison.OrdinalIgnoreCase))
                    {
                        cancelSource.Cancel();
                        break;
                    }

                    var destinationStep = this._steps.First(v => v.Id == message.DestinationId);

                    // Send a message to the step
                    messageTasks.Add(destinationStep.HandleMessageAsync(message));
                    finalStep = destinationStep;
                }

                await Task.WhenAll(messageTasks).ConfigureAwait(false);

                // Check for cancellation
                if (cancelSource.IsCancellationRequested)
                {
                    return;
                }
            }
        }
        catch (Exception)
        {
            throw;
        }
        finally
        {
            if (!cancelSource.IsCancellationRequested)
            {
                cancelSource.Cancel();
            }
            cancelSource.Dispose();
        }

        return;
    }

    private void EnqueueStepMessagesAsync(LocalStep step, Kernel kernel, Queue<LocalMessage> messageChannel)
    {
        // Process all of the messages that have been sent to this step
        var allStepEvents = step.GetAllEvents();
        foreach (var stepEvent in allStepEvents)
        {
            foreach (var edge in step.GetEdgeForEvent(stepEvent.Id!))
            {
                var target = edge.OutputTarget;
                Dictionary<string, object?> parameterValue = new();
                if (!string.IsNullOrWhiteSpace(target.ParameterName))
                {
                    parameterValue.Add(target.ParameterName!, stepEvent.Data);
                }

                LocalMessage newMessage = new(edge.SourceStepId, target.StepId, target.FunctionName, parameterValue);
                messageChannel.Enqueue(newMessage);
            }
        }
    }
}
