// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Runtime;

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

        //Console.WriteLine($"\tLOCAL MAP: {map.State.Id}");

        this._map = map;
        this._logger = this.LoggerFactory?.CreateLogger<LocalMap>() ?? new NullLogger<LocalMap>();
    }

    /// <inheritdoc/>
    internal override async Task HandleMessageAsync(ProcessMessage message)
    {
        IEnumerable values = message.GetMapInput(this._map.InputParameterName, this._logger);

        int index = 0;
        List<Task<LocalKernelProcessContext>> runningProcesses = [];
        foreach (var value in values)
        {
            ++index;
            Console.WriteLine($"#{index}: {value}");
            runningProcesses.Add(
                this._map.MapStep.CloneProcess(this._logger).StartAsync(
                    this._kernel,
                    new KernelProcessEvent
                    {
                        Id = KernelProcessMap.MapEventId,
                        Data = value
                    }));
        }

        await Task.WhenAll(runningProcesses).ConfigureAwait(false);

        Array? results = null;

        for (index = 0; index < runningProcesses.Count; ++index)
        {
            KernelProcess mapProcess = await runningProcesses[index].Result.GetStateAsync().ConfigureAwait(false);
            object result = mapProcess.GetMapOutput();

            if (results == null)
            {
                Type elementType = result.GetType(); // %%% NO RESULT ON FAILURE
                results = Array.CreateInstance(elementType, runningProcesses.Count); // %%% CONSTRAINS RECEIVING SIGNATURE (NOT List<T>)
            }

            results.SetValue(result, index);
        }

        //Console.WriteLine($"LOCAL MAP: OUTPUT: {string.Join(",", [.. results])}");

        await this.EmitEventAsync(new() { Id = this._map.CompleteEventId, Data = results }).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    protected override ValueTask InitializeStepAsync()
    {
        // The map does not need any further initialization as it's already been initialized.
        // Override the base method to prevent it from being called.
        return default;
    }
}
