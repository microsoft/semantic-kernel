// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel;

internal sealed class LocalMap : LocalStep
{
    private readonly KernelProcessMap _map;
    private readonly ILogger _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="LocalMap"/> class.
    /// </summary>
    /// <param name="map">The <see cref="KernelProcessMap"/> instance.</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    /// <param name="parentProcessId">Optional. The Id of the parent process if one exists, otherwise null.</param>
    /// <param name="loggerFactory">Optional. A <see cref="ILoggerFactory"/>.</param>
    internal LocalMap(KernelProcessMap map, Kernel kernel, string? parentProcessId = null, ILoggerFactory? loggerFactory = null)
        : base(map, kernel, parentProcessId, loggerFactory)
    {
        Verify.NotNull(map.MapStep);

        Console.WriteLine($"LOCAL MAP: [{map.MapStep.Steps.Count}] {string.Join(",", map.MapStep.Steps.Select(s => s.InnerStepType.Name))} - {this.Id} [{parentProcessId ?? "-"}]");

        this._map = map;
        this._logger = this.LoggerFactory?.CreateLogger(this.Name) ?? new NullLogger<LocalMap>();
    }

    /// <inheritdoc/>
    internal override async Task HandleMessageAsync(LocalMessage message)
    {
        if (string.IsNullOrWhiteSpace(message.TargetEventId))
        {
            string errorMessage = "Internal Map Error: The target event id must be specified when sending a message to a step.";
            this._logger.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException(errorMessage);
        }

        if (!message.Values.TryGetValue(this._map.InputParameterName, out object? values))
        {
            throw new KernelException($"Internal Map Error: Input parameter not present - {this._map.InputParameterName}");
        }

        Type valueType = values!.GetType();
        if (!typeof(IEnumerable).IsAssignableFrom(valueType) || !valueType.HasElementType)
        {
            throw new KernelException($"Internal Map Error: Input parameter is not enumerable - {this._map.InputParameterName} [{valueType.FullName}]");
        }

        int index = 0;
        List<Task<LocalKernelProcessContext>> runningProcesses = [];
        foreach (var value in (IEnumerable)values)
        {
            ++index;
            Console.WriteLine($"#{index}: {value}");
            runningProcesses.Add(
                this._map.MapStep.StartAsync(
                    this._kernel,
                    new KernelProcessEvent
                    {
                        Id = message.TargetEventId,
                        Data = value
                    }));
        }

        await Task.WhenAll(runningProcesses).ConfigureAwait(false);

        Array? results = null;

        for (index = 0; index < runningProcesses.Count; ++index)
        {
            var processInfo = await runningProcesses[index].Result.GetStateAsync().ConfigureAwait(false);
            KernelProcessStepState state =
                processInfo.Steps
                    .Where(step => step.Edges.Count == 0)
                    .Single()
                    .State;
            object resultState = state.GetType().GetProperty("State")!.GetValue(state)!; // %%% NULLABLE / TYPE ASSUMPTION (CLEAN-UP)
            object result = resultState.GetType().GetProperty("Value")!.GetValue(resultState)!; // %%% NULLABLE / TYPE ASSUMPTION (CLEAN-UP)
            if (results == null)
            {
                Type elementType = result.GetType();
                results = Array.CreateInstance(elementType, runningProcesses.Count);
            }

            results.SetValue(result, index);
        }

        Console.WriteLine($"LOCAL MAP: OUTPUT: {string.Join(",", [.. results])}");

        await this.EmitEventAsync(new() { Id = this._map.CompleteEventId, Data = results, Visibility = KernelProcessEventVisibility.Public }).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    protected override ValueTask InitializeStepAsync()
    {
        // The map does not need any further initialization as it's already been initialized.
        // Override the base method to prevent it from being called.
        return default;
    }
}
