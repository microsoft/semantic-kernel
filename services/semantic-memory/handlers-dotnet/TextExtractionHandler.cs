// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Services.DataFormats.Office;
using Microsoft.SemanticKernel.Services.DataFormats.Pdf;
using Microsoft.SemanticKernel.Services.Diagnostics;
using Microsoft.SemanticKernel.Services.Storage.Pipeline;

namespace Microsoft.SemanticKernel.Services.SemanticMemory.Handlers;

public class TextExtractionHandler : IHostedService, IPipelineStepHandler
{
    private readonly IPipelineOrchestrator _orchestrator;
    private readonly ILogger<TextExtractionHandler> _log;

    public TextExtractionHandler(
        string stepName,
        IPipelineOrchestrator orchestrator,
        ILogger<TextExtractionHandler>? log = null)
    {
        this.StepName = stepName;
        this._orchestrator = orchestrator;
        this._log = log ?? NullLogger<TextExtractionHandler>.Instance;
    }

    /// <inheritdoc />
    public string StepName { get; }

    /// <inheritdoc />
    public Task StartAsync(CancellationToken cancellationToken)
    {
        this.LogStart();
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
        foreach (DataPipeline.FileDetails file in pipeline.Files)
        {
            var sourceFile = file.Name;
            var destFile = $"{file.Name}.extract.txt";
            BinaryData fileContent = await this._orchestrator.ReadFileAsync(pipeline, sourceFile, cancellationToken);
            string text = string.Empty;

            switch (file.Type)
            {
                case MimeTypes.PlainText:
                    text = fileContent.ToString();
                    break;

                case MimeTypes.MsWord:
                    text = new MsWordDecoder().DocToText(fileContent);
                    break;

                case MimeTypes.Pdf:
                    text = new PdfDecoder().DocToText(fileContent);
                    break;

                default:
                    throw new NotSupportedException($"File type not supported: {file.Type}");
            }

            await this._orchestrator.WriteFileAsync(pipeline, destFile, BinaryData.FromString(text), cancellationToken);

            file.GeneratedFiles.Add(destFile);
        }

        return (true, pipeline);
    }

    private void LogStart()
    {
        this._log.LogInformation(
            "Starting {0}, Log Level: {1}, .NET Env: {2}",
            this.GetType().Name,
            this._log.GetLogLevelName(),
            Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT"));
    }
}
