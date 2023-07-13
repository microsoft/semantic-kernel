// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Services.Storage.Pipeline;

public interface IPipelineStepHandler
{
    /// <summary>
    /// Name of the pipeline step assigned to the handler
    /// </summary>
    string StepName { get; }

    /// <summary>
    /// Method invoked by semantic memory orchestrators to process a pipeline.
    /// The method is invoked only when the next step in the pipeline matches
    /// with the name handled by the handler. See <see cref="IPipelineOrchestrator.AttachHandlerAsync"/>
    /// </summary>
    /// <param name="pipeline">Pipeline status</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    /// <returns>Whether the pipeline step has been processed successfully, and the new pipeline status to use moving forward</returns>
    Task<(bool success, DataPipeline updatedPipeline)> InvokeAsync(DataPipeline pipeline, CancellationToken cancellationToken);
}
