// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Text;
using SemanticKernel.Service.Auth;
using SemanticKernel.Service.CopilotChat.Models;
using SemanticKernel.Service.CopilotChat.Options;
using SemanticKernel.Service.CopilotChat.Storage;
using UglyToad.PdfPig;
using UglyToad.PdfPig.DocumentLayoutAnalysis.TextExtractor;

namespace SemanticKernel.Service.CopilotChat.Controllers;

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

    private readonly ILogger<DocumentImportController> _logger;
    private readonly DocumentMemoryOptions _options;
    private readonly ChatSessionRepository _chatSessionRepository;

    /// <summary>
    /// Initializes a new instance of the <see cref="DocumentImportController"/> class.
    /// </summary>
    public DocumentImportController(
        IOptions<DocumentMemoryOptions> documentMemoryOptions,
        ILogger<DocumentImportController> logger,
        ChatSessionRepository chatSessionRepository)
    {
        this._options = documentMemoryOptions.Value;
        this._logger = logger;
        this._chatSessionRepository = chatSessionRepository;
    }

    /// <summary>
    /// Service API for importing a document.
    /// </summary>
    [Route("importDocument")]
    [HttpPost]
    [ProducesResponseType(StatusCodes.Status202Accepted)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> ImportDocumentAsync(
        [FromServices] IKernel kernel,
        [FromServices] IAuthInfo authInfo,
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

        if (documentImportForm.DocumentScope == DocumentImportForm.DocumentScopes.Chat)
        {
            var chatSession = await this._chatSessionRepository.FindByIdAsync(documentImportForm.ChatId.ToString());
            if (chatSession == null)
            {
                return this.NotFound("Session does not exist.");
            }

            if (authInfo.UserId != chatSession.UserId)
            {
                return this.Unauthorized("User does not have access to the chat session.");
            }
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

        return this.Accepted();
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
            : this._options.ChatDocumentCollectionNamePrefix + documentImportForm.ChatId;

        // Split the document into lines of text and then combine them into paragraphs.
        // Note that this is only one of many strategies to chunk documents. Feel free to experiment with other strategies.
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
