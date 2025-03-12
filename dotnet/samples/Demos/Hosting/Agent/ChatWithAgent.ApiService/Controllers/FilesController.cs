// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace ChatWithAgent.ApiService;

/// <summary>
/// Controller for managing files.
/// </summary>
[ApiController]
[Route("files")]

public sealed class FilesController : ControllerBase
{
    private readonly IDataLoader _dataLoader;
    private readonly ILogger<FilesController> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="FilesController"/> class.
    /// </summary>
    /// <param name="dataLoader">The data loader.</param>
    /// <param name="logger">The logger.</param>
    public FilesController(IDataLoader dataLoader, ILogger<FilesController> logger)
    {
        this._dataLoader = dataLoader;
        this._logger = logger;
    }

    /// <summary>
    /// Uploads files.
    /// </summary>
    /// <param name="files">The files to upload.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    [HttpPost]
    public async Task<IActionResult> UploadFilesAsync([FromForm] List<IFormFile> files, CancellationToken cancellationToken)
    {
        if (files == null || files.Count == 0)
        {
            return this.BadRequest("No files received.");
        }

        foreach (var file in files)
        {
            if (file.ContentType != "application/pdf")
            {
                return this.BadRequest("Only PDF files are allowed.");
            }

            using var stream = file.OpenReadStream();

            await this._dataLoader.LoadPdfAsync(stream, file.FileName, cancellationToken).ConfigureAwait(false);
        }

        return this.Ok("Files uploaded successfully.");
    }
}
