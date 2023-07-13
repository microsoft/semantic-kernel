// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;

namespace Microsoft.SemanticKernel.Services.Storage.Pipeline;

public interface IPipelineOrchestrator
{
    /// <summary>
    /// Attach a handler for a specific task
    /// </summary>
    /// <param name="handler">Handler instance</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    Task AttachHandlerAsync(IPipelineStepHandler handler, CancellationToken cancellationToken = default);

    /// <summary>
    /// Create a new pipeline value object for files upload
    /// </summary>
    /// <param name="id">Id of the pipeline instance. This value will persist throughout the pipeline and final data lineage used for citations.</param>
    /// <param name="userId">Primary user who the data belongs to. Other users, e.g. sharing, is not supported in the pipeline at this time.</param>
    /// <param name="vaultIds">List of vaults where o store the semantic memory extracted from the files. E.g. "chat ID", "personal", etc.</param>
    /// <param name="filesToUpload">List of files provided before starting the pipeline, to be uploaded into the container before starting.</param>
    /// <returns>Pipeline representation</returns>
    DataPipeline PrepareNewFileUploadPipeline(string id, string userId, IEnumerable<string> vaultIds, IEnumerable<IFormFile> filesToUpload);

    /// <summary>
    /// Create a new pipeline value object, with an empty list of files
    /// </summary>
    /// <param name="id">Id of the pipeline instance. This value will persist throughout the pipeline and final data lineage used for citations.</param>
    /// <param name="userId">Primary user who the data belongs to. Other users, e.g. sharing, is not supported in the pipeline at this time.</param>
    /// <param name="vaultIds">List of vaults where o store the semantic memory extracted from the files. E.g. "chat ID", "personal", etc.</param>
    /// <returns>Pipeline representation</returns>
    DataPipeline PrepareNewFileUploadPipeline(string id, string userId, IEnumerable<string> vaultIds);

    /// <summary>
    /// Start a new data pipeline execution
    /// </summary>
    /// <param name="pipeline">Pipeline to execute</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    Task RunPipelineAsync(DataPipeline pipeline, CancellationToken cancellationToken = default);

    /// <summary>
    /// Stop all the pipelines in progress
    /// </summary>
    Task StopAllPipelinesAsync();

    /// <summary>
    /// Fetch a file from content storage
    /// </summary>
    /// <param name="pipeline">Pipeline containing the file</param>
    /// <param name="fileName">Name of the file to fetch</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    Task<BinaryData> ReadFileAsync(DataPipeline pipeline, string fileName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Fetch a file from content storage
    /// </summary>
    /// <param name="pipeline">Pipeline containing the file</param>
    /// <param name="fileName">Name of the file to fetch</param>
    /// <param name="fileContent">File content</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    Task WriteFileAsync(DataPipeline pipeline, string fileName, BinaryData fileContent, CancellationToken cancellationToken = default);
}
