// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel.Services.Storage.Pipeline;

/// <summary>
/// Work in progress, client not ready
/// TODO: organize dependencies, split IHost and IPipelineStepHandler
/// </summary>
public class SemanticMemoryClient
{
    private readonly IPipelineOrchestrator _orchestrator;

    private readonly IPipelineStepHandler? _textExtraction = null;

    public SemanticMemoryClient(IServiceProvider services) : this(services.GetService<IPipelineOrchestrator>()!)
    {
        // this._textExtraction = new TextExtractionHandler("extract", this._orchestrator);
    }

    public SemanticMemoryClient(IPipelineOrchestrator orchestrator)
    {
        this._orchestrator = orchestrator;
    }

    public Task ImportFileAsync(string file, string userid, string vaultId)
    {
        return this.ImportFileAsync(file, userid, new[] { vaultId });
    }

    public async Task ImportFileAsync(string file, string userid, string[] vaults)
    {
        // Attach handlers
        await this._orchestrator.AttachHandlerAsync(this._textExtraction!).ConfigureAwait(false);

        var pipeline = this._orchestrator
            .PrepareNewFileUploadPipeline(Guid.NewGuid().ToString("D"), userid, vaults)
            .AddUploadFile("file1", file, file)
            .Then("extract")
            // .Then("partition")
            // .Then("index")
            .Build();

        // Execute pipeline
        await this._orchestrator.RunPipelineAsync(pipeline).ConfigureAwait(false);
    }
}
