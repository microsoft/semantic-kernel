// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

internal sealed class LocalMap : LocalStep
{
    private readonly HashSet<string> _mapEvents;
    private readonly KernelProcessMap _map;
    private readonly ILogger _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="LocalMap"/> class.
    /// </summary>
    /// <param name="map">The <see cref="KernelProcessMap"/> instance.</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    internal LocalMap(KernelProcessMap map, Kernel kernel)
        : base(map, kernel)
    {
        this._map = map;
        this._logger = this._kernel.LoggerFactory?.CreateLogger(this._map.State.Name) ?? new NullLogger<LocalStep>();
        this._mapEvents = [.. map.Edges.Keys.Select(key => key.Split(ProcessConstants.EventIdSeparator).Last())];
    }

    /// <inheritdoc/>
    internal override async Task HandleMessageAsync(ProcessMessage message)
    {
        // Initialize the current operation
        (IEnumerable inputValues, KernelProcess mapOperation, string startEventId) = this._map.Initialize(message, this._logger);

        // Prepare state for map execution
        int index = 0;
        List<(Task Task, LocalKernelProcessContext ProcessContext, MapOperationContext Context)> mapOperations = [];
        ConcurrentDictionary<string, Type> capturedEvents = [];
        try
        {
            // Execute the map operation for each value
            foreach (var value in inputValues)
            {
                ++index;

                KernelProcess process = mapOperation.CloneProcess(this._logger);
                MapOperationContext context = new(this._mapEvents, capturedEvents);
#pragma warning disable CA2000 // Dispose objects before losing scope
                LocalKernelProcessContext processContext = new(process, this._kernel, context.Filter);
                Task processTask =
                    processContext.StartWithEventAsync(
                        new KernelProcessEvent
                        {
                            Id = startEventId,
                            Data = value
                        });
#pragma warning restore CA2000 // Dispose objects before losing scope

                mapOperations.Add((processTask, processContext, context));
            }

            // Wait for all the map operations to complete
            await Task.WhenAll(mapOperations.Select(p => p.Task)).ConfigureAwait(false);

            // Correlate the operation results to emit as the map result
            Dictionary<string, Array> resultMap = [];
            for (index = 0; index < mapOperations.Count; ++index)
            {
                foreach (KeyValuePair<string, Type> capturedEvent in capturedEvents)
                {
                    string eventName = capturedEvent.Key;
                    Type resultType = capturedEvent.Value;

                    mapOperations[index].Context.Results.TryGetValue(eventName, out object? result);
                    if (result is KernelProcessEventData eventData)
                    {
                        result = eventData.ToObject();
                        resultType = Type.GetType(eventData.ObjectType)!;
                    }

                    if (!resultMap.TryGetValue(eventName, out Array? results))
                    {
                        results = Array.CreateInstance(resultType, mapOperations.Count);
                        resultMap[eventName] = results;
                    }

                    results.SetValue(result, index);
                }
            }

            // Emit map results
            foreach (string eventName in capturedEvents.Keys)
            {
                Array eventResult = resultMap[eventName];
                await this.EmitEventAsync(new() { Id = eventName, Data = eventResult }).ConfigureAwait(false);
            }
        }
        finally
        {
            foreach (var operation in mapOperations)
            {
                await operation.ProcessContext.DisposeAsync().ConfigureAwait(false);
            }
        }
    }

    /// <inheritdoc/>
    protected override ValueTask InitializeStepAsync()
    {
        // The map does not need any further initialization as it's already been initialized.
        // Override the base method to prevent it from being called.
        return default;
    }

    private sealed record MapOperationContext(in HashSet<string> EventTargets, in IDictionary<string, Type> CapturedEvents)
    {
        public ConcurrentDictionary<string, object?> Results { get; } = [];

        public bool Filter(ProcessEvent processEvent)
        {
            string eventName = processEvent.SourceId;
            if (this.EventTargets.Contains(eventName))
            {
                this.CapturedEvents.TryGetValue(eventName, out Type? resultType);
                if (resultType is null || resultType == typeof(object))
                {
                    this.CapturedEvents[eventName] = processEvent.Data?.GetType() ?? typeof(object);
                }

                this.Results[eventName] = processEvent.Data;
            }

            return true;
        }
    }
}
