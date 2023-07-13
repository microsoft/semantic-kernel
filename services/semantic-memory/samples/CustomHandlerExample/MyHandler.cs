// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Services.Storage.Pipeline;

public class MyHandler : IHostedService, IPipelineStepHandler
{
    private readonly IPipelineOrchestrator _orchestrator;
    private readonly ILogger<MyHandler> _log;

    public MyHandler(
        string stepName,
        IPipelineOrchestrator orchestrator,
        ILogger<MyHandler>? log = null)
    {
        this.StepName = stepName;
        this._orchestrator = orchestrator;
        this._log = log ?? NullLogger<MyHandler>.Instance;
    }

    /// <inheritdoc />
    public string StepName { get; }

    /// <inheritdoc />
    public Task StartAsync(CancellationToken cancellationToken)
    {
        return this._orchestrator.AttachHandlerAsync(this, cancellationToken);
    }

    /// <inheritdoc />
    public Task StopAsync(CancellationToken cancellationToken)
    {
        return this._orchestrator.StopAllPipelinesAsync();
    }

    /// <inheritdoc />
    public async Task<(bool success, DataPipeline updatedPipeline)> InvokeAsync(DataPipeline pipeline, CancellationToken cancellationToken)
    {
        // ... your custom handler business logic ...

        // Remove this - here only to avoid build errors
        await Task.Delay(0, cancellationToken);

        return (true, pipeline);
    }
}
