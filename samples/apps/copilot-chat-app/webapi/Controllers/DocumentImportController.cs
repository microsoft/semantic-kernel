// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel;
using SemanticKernel.Service.Model;
using SemanticKernel.Service.Skills;

namespace SemanticKernel.Service.Controllers;

/// <summary>
/// Controller for importing documents.
/// </summary>
[ApiController]
public class DocumentImportController : ControllerBase
{
    /// <summary>
    /// Supported file types for import.
    /// </summary>
    internal enum SupportedFileType
    {
        TXT,    // .txt
        PDF,    // .pdf
    };
    private readonly IServiceProvider _serviceProvider;
    private readonly IConfiguration _configuration;
    private readonly ILogger<DocumentImportController> _logger;
    private readonly PromptSettings _promptSettings;

    /// <summary>
    /// Initializes a new instance of the <see cref="DocumentImportController"/> class.
    /// </summary>
    public DocumentImportController(IServiceProvider serviceProvider, IConfiguration configuration, PromptSettings promptSettings, ILogger<DocumentImportController> logger)
    {
        this._serviceProvider = serviceProvider;
        this._configuration = configuration;
        this._promptSettings = promptSettings;
        this._logger = logger;
    }

    /// <summary>
    /// Service API for importing a document.
    /// </summary>
    [Authorize]
    [Route("importDocument")]
    [HttpPost]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> ImportDocumentAsync([FromServices] Kernel kernel, [FromForm] FileModel file)
    {
        if (file.FormFile == null)
        {
            return this.BadRequest("No file was uploaded.");
        }

        if (file.FormFile.Length == 0)
        {
            return this.BadRequest("File is empty.");
        }

        // TODO: set a max file size limit
        this._logger.LogInformation("Importing document {0}", file.FormFile.FileName);

        try
        {
            var fileType = this.GetFileType(Path.GetFileName(file.FormFile.FileName));
            var fileContent = string.Empty;
            switch (fileType)
            {
                case SupportedFileType.TXT:
                    fileContent = await this.ReadTxtFileAsync(file.FormFile);
                    break;
                case SupportedFileType.PDF:
                    fileContent = await this.ReadPdfFileAsync(file.FormFile);
                    break;
                default:
                    break;
            }
        }
        catch (Exception e)
        {
            return this.BadRequest(e.Message);
        }

        return this.Ok();
    }

    /// <summary>
    /// Get the file type from the file extension.
    /// </summary>
    /// <param name="fileName">Name of the file.</param>
    /// <returns>A SupportedFileType.</returns>
    /// <exception cref="ArgumentOutOfRangeException"></exception>
    private SupportedFileType GetFileType(string fileName)
    {
        string extension = Path.GetExtension(fileName);
        switch (extension)
        {
            case ".txt":
                return SupportedFileType.TXT;
            case ".pdf":
                return SupportedFileType.PDF;
            default:
                throw new ArgumentOutOfRangeException($"Unsupported file type: {extension}");
        }
    }

    /// <summary>
    /// Read the content of a text file.
    /// </summary>
    /// <param name="file">An IFormFile object.</param>
    /// <returns>A string of the content of the file.</returns>
    private async Task<string> ReadTxtFileAsync(IFormFile file)
    {
        return await new StreamReader(file.OpenReadStream()).ReadToEndAsync();
    }

    /// <summary>
    /// Read the content of a PDF file.
    /// </summary>
    /// <param name="file">An IFormFile object.</param>
    /// <returns>A string of the content of the file.</returns>
    private async Task<string> ReadPdfFileAsync(IFormFile file)
    {
        return await new StreamReader(file.OpenReadStream()).ReadToEndAsync();
    }
}