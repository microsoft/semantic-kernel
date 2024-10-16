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
        Verify.NotNull(map.TransformStep);

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

        var values = message.Values["values"];
        Type valueType = values?.GetType() ?? typeof(object);

        IEnumerable enumerable = values == null ? new DiscreteEnumerable() : typeof(IEnumerable).IsAssignableFrom(valueType) ? (IEnumerable)values : new DiscreteEnumerable(values);

        Console.WriteLine(this._map.TransformStep.GetType());

        int index = 0;
        List<Task<LocalKernelProcessContext>> runningProcesses = [];
        foreach (var value in enumerable)
        {
            ++index;
            Console.WriteLine($"#{index}: {value}");
            runningProcesses.Add(
                this._map.TransformStep.StartAsync(
                    this._kernel,
                    new KernelProcessEvent
                    {
                        Id = "Start", // %%% MORE this._map.StartId,
                        Data = value
                    }));
        }

        await Task.WhenAll(runningProcesses).ConfigureAwait(false);

        //return Task.CompletedTask; // %%% TODO - BIG!
    }

    private class DiscreteEnumerable(object? value = null) : IEnumerable
    {
        public IEnumerator GetEnumerator() => new DiscreteEnumerator(value);
    }

    private class DiscreteEnumerator(object? value) : IEnumerator
    {
        private int _index = 0;

        public object Current => this._index == 0 && value != null ? value : throw new InvalidOperationException();

        public bool MoveNext() => !(value == null || this._index == 0);

        public void Reset() { this._index = 0; }
    }

    #region Private Methods

    /// <summary>
    /// Loads the process and initializes the steps. Once this is complete the process can be started.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    private ValueTask InitializeMapAsync()
    {
        return default;
    }

    /// <inheritdoc/>
    protected override ValueTask InitializeStepAsync()
    {
        // The process does not need any further initialization as it's already been initialized.
        // Override the base method to prevent it from being called.
        return default;
    }

    #endregion
}
