// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Text;
using SemanticKernel.Service.Config;
using SemanticKernel.Service.Model;
using SemanticKernel.Service.Skills;
using UglyToad.PdfPig;
using UglyToad.PdfPig.DocumentLayoutAnalysis.TextExtractor;

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
    private enum SupportedFileType
    {
        /// <summary>
        /// .txt
        /// </summary>
        Txt,

        /// <summary>
        /// .pdf
        /// </summary>
        Pdf,
    };

    private readonly IServiceProvider _serviceProvider; // TODO: unused
    private readonly ILogger<DocumentImportController> _logger;
    private readonly PromptSettings _promptSettings; // TODO: unused
    private readonly DocumentMemoryOptions _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="DocumentImportController"/> class.
    /// </summary>
    public DocumentImportController(
        IServiceProvider serviceProvider,
        PromptSettings promptSettings,
        IOptions<DocumentMemoryOptions> documentMemoryOptions,
        ILogger<DocumentImportController> logger)
    {
        this._serviceProvider = serviceProvider;
        this._options = documentMemoryOptions.Value;
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
    public async Task<IActionResult> ImportDocumentAsync(
        [FromServices] IKernel kernel,
        [FromForm] DocumentImportForm documentImportForm)
    {
        var formFile = documentImportForm.FormFile;
        if (formFile == null)
        {
            return this.BadRequest("No file was uploaded.");
        }

        if (formFile.Length == 0)
        {
            return this.BadRequest("File is empty.");
        }

        if (formFile.Length > this._options.FileSizeLimit)
        {
            return this.BadRequest("File size exceeds the limit.");
        }

        this._logger.LogInformation("Importing document {0}", formFile.FileName);

        try
        {
            var fileType = this.GetFileType(Path.GetFileName(formFile.FileName));
            var fileContent = string.Empty;
            switch (fileType)
            {
                case SupportedFileType.Txt:
                    fileContent = await this.ReadTxtFileAsync(formFile);
                    break;
                case SupportedFileType.Pdf:
                    fileContent = this.ReadPdfFile(formFile);
                    break;
                default:
                    return this.BadRequest($"Unsupported file type: {fileType}");
            }

            await this.ParseDocumentContentToMemoryAsync(kernel, fileContent, documentImportForm);
        }
        catch (Exception ex) when (ex is ArgumentOutOfRangeException)
        {
            return this.BadRequest(ex.Message);
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
        return extension switch
        {
            ".txt" => SupportedFileType.Txt,
            ".pdf" => SupportedFileType.Pdf,
            _ => throw new ArgumentOutOfRangeException($"Unsupported file type: {extension}"),
        };
    }

    /// <summary>
    /// Read the content of a text file.
    /// </summary>
    /// <param name="file">An IFormFile object.</param>
    /// <returns>A string of the content of the file.</returns>
    private async Task<string> ReadTxtFileAsync(IFormFile file)
    {
        using var streamReader = new StreamReader(file.OpenReadStream());
        return await streamReader.ReadToEndAsync();
    }

    /// <summary>
    /// Read the content of a PDF file, ignoring images.
    /// </summary>
    /// <param name="file">An IFormFile object.</param>
    /// <returns>A string of the content of the file.</returns>
    private string ReadPdfFile(IFormFile file)
    {
        var fileContent = string.Empty;

        using var pdfDocument = PdfDocument.Open(file.OpenReadStream());
        foreach (var page in pdfDocument.GetPages())
        {
            var text = ContentOrderTextExtractor.GetText(page);
            fileContent += text;
        }

        return fileContent;
    }

    /// <summary>
    /// Parse the content of the document to memory.
    /// </summary>
    /// <param name="kernel">The kernel instance from the service</param>
    /// <param name="content">The file content read from the uploaded document</param>
    /// <param name="documentImportForm">The document upload form that contains additional necessary info</param>
    /// <returns></returns>
    private async Task ParseDocumentContentToMemoryAsync(IKernel kernel, string content, DocumentImportForm documentImportForm)
    {
        var documentName = Path.GetFileName(documentImportForm.FormFile?.FileName);
        var targetCollectionName = documentImportForm.DocumentScope == DocumentImportForm.DocumentScopes.Global
            ? this._options.GlobalDocumentCollectionName
            : string.IsNullOrEmpty(documentImportForm.UserId)
                ? this._options.GlobalDocumentCollectionName
                : this._options.UserDocumentCollectionNamePrefix + documentImportForm.UserId;

        // Split the document into lines of text and then combine them into paragraphs.
        // NOTE that this is only one of the strategies to chunk documents. Feel free to experiment with other strategies.
        var lines = TextChunker.SplitPlainTextLines(content, this._options.DocumentLineSplitMaxTokens);
        var paragraphs = TextChunker.SplitPlainTextParagraphs(lines, this._options.DocumentParagraphSplitMaxLines);

        foreach (var paragraph in paragraphs)
        {
            await kernel.Memory.SaveInformationAsync(
                collection: targetCollectionName,
                text: paragraph,
                id: Guid.NewGuid().ToString(),
                description: $"Document: {documentName}");
        }

        this._logger.LogInformation(
            "Parsed {0} paragraphs from local file {1}",
            paragraphs.Count,
            Path.GetFileName(documentImportForm.FormFile?.FileName)
        );
    }
}
