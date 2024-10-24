// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

internal sealed class LocalMap : LocalStep
{
    private readonly HashSet<string> _mapEvents;
    private readonly KernelProcessMap _map;
    private ILogger? _logger;
    private ILogger Logger => this._logger ??= this.LoggerFactory?.CreateLogger(this.Name) ?? NullLogger.Instance;

    /// <summary>
    /// Initializes a new instance of the <see cref="LocalMap"/> class.
    /// </summary>
    /// <param name="map">The <see cref="KernelProcessMap"/> instance.</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    internal LocalMap(KernelProcessMap map, Kernel kernel)
        : base(map, kernel)
    {
        Verify.NotNull(map.Operation);

        this._map = map;

        Console.WriteLine($"\tLOCAL MAP: {this._map.State.Id}");
        this._mapEvents = [.. map.Edges.Keys.Select(key => key.Split('.').Last())];
        //this._mapEvents = [.. this._map.Edges.Keys];
        foreach (var eventName in this._mapEvents)
        {
            Console.WriteLine($"\tLOCAL MAP EDGE: {eventName}");
        }
    }

    /// <inheritdoc/>
    internal override async Task HandleMessageAsync(ProcessMessage message)
    {
        IEnumerable values = message.GetMapInput(this._map.InputParameterName, this.Logger);

        int index = 0;
        List<(Task<LocalKernelProcessContext> Task, MapOperationContext Context)> runningProcesses = [];
        Dictionary<string, Type> capturedEvents = [];

        try
        {
            foreach (var value in values)
            {
                ++index;
                Console.WriteLine($"\tLOCAL MAP #{index}: {value}");

                KernelProcess process = this._map.Operation.CloneProcess(this.Logger);
                MapOperationContext context = new(index, this._mapEvents, capturedEvents);
#pragma warning disable CA2000 // Dispose objects before losing scope
                Task<LocalKernelProcessContext> processTask =
                    this.StartProcessAsync(
                        process,
                        new KernelProcessEvent
                        {
                            Id = KernelProcessMap.MapEventId,
                            Data = value
                        },
                        context.Filter);
#pragma warning restore CA2000 // Dispose objects before losing scope

                runningProcesses.Add((processTask, context));
            }

            await Task.WhenAll(runningProcesses.Select(p => p.Task)).ConfigureAwait(false);

            Dictionary<string, Array> resultMap = [];

            for (index = 0; index < runningProcesses.Count; ++index)
            {
                foreach (var capturedEvent in capturedEvents)
                {
                    string eventName = capturedEvent.Key;
                    Type resultType = capturedEvent.Value;

                    runningProcesses[index].Context.Results.TryGetValue(eventName, out object? result);
                    if (!resultMap.TryGetValue(eventName, out Array? results))
                    {
                        results = Array.CreateInstance(resultType, runningProcesses.Count); // %%% CONSTRAINS RECEIVING SIGNATURE (NOT List<T>)
                        resultMap[eventName] = results;
                    }

                    results.SetValue(result, index);
                }
            }

            foreach (var capturedEvent in capturedEvents)
            {
                string eventName = capturedEvent.Key;
                Array eventResult = resultMap[eventName];
                Console.WriteLine($"LOCAL MAP: OUTPUT: {eventName} - {string.Join(",", [.. eventResult])}");
                await this.EmitEventAsync(new() { Id = eventName, Data = eventResult }).ConfigureAwait(false);
            }
        }
        finally
        {
            foreach (var process in runningProcesses)
            {
                process.Task.Result.Dispose();
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

    private async Task<LocalKernelProcessContext> StartProcessAsync(KernelProcess process, KernelProcessEvent initialEvent, ProcessEventFilter filter)
    {
        LocalKernelProcessContext processContext = new(process, this._kernel, filter);

        await processContext.StartWithEventAsync(initialEvent).ConfigureAwait(false);

        return processContext;
    }

    private sealed record MapOperationContext(int Index, HashSet<string> EventTargets, Dictionary<string, Type> CapturedEvents)
    {
        public Dictionary<string, object?> Results { get; } = [];

        public bool Filter(KernelProcessEvent processEvent)
        {
            if (!string.IsNullOrEmpty(processEvent.Id))
            {
                string eventName = processEvent.Id!;
                if (this.EventTargets.Contains(eventName))
                {
                    Console.WriteLine($"\tFILTER CAPTURE: {eventName} {processEvent.Data}");

                    this.CapturedEvents.TryGetValue(eventName, out Type? resultType);
                    if (resultType is null || resultType == typeof(object))
                    {
                        this.CapturedEvents[eventName] = processEvent.Data?.GetType() ?? typeof(object);
                    }

                    this.Results[eventName] = processEvent.Data;

                    return false;
                }
            }

            return true;
        }
    }
}
