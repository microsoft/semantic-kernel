// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Text;
using SemanticKernel.Service.CopilotChat.Models;
using SemanticKernel.Service.CopilotChat.Options;
using SemanticKernel.Service.CopilotChat.Storage;
using UglyToad.PdfPig;
using UglyToad.PdfPig.DocumentLayoutAnalysis.TextExtractor;
using static SemanticKernel.Service.CopilotChat.Models.MemorySource;

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
    private readonly ChatSessionRepository _sessionRepository;
    private readonly ChatMemorySourceRepository _sourceRepository;

    /// <summary>
    /// Initializes a new instance of the <see cref="DocumentImportController"/> class.
    /// </summary>
    public DocumentImportController(
        IOptions<DocumentMemoryOptions> documentMemoryOptions,
        ILogger<DocumentImportController> logger,
        ChatSessionRepository sessionRepository,
        ChatMemorySourceRepository sourceRepository)
    {
        this._options = documentMemoryOptions.Value;
        this._logger = logger;
        this._sessionRepository = sessionRepository;
        this._sourceRepository = sourceRepository;
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

        if (documentImportForm.DocumentScope == DocumentImportForm.DocumentScopes.Chat
            && !(await this.UserHasAccessToChatAsync(documentImportForm.UserId, documentImportForm.ChatId)))
        {
            return this.BadRequest("User does not have access to the chat session.");
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

            var memorySource = new MemorySource(
                documentImportForm.ChatId.ToString(),
                formFile.FileName,
                documentImportForm.UserId,
                MemorySourceType.File,
                null);

            await this._sourceRepository.UpsertAsync(memorySource);

            try
            {
                await this.ParseDocumentContentToMemoryAsync(kernel, fileContent, documentImportForm, memorySource.Id);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                await this._sourceRepository.DeleteAsync(memorySource);
                throw;
            }
        }
        catch (ArgumentOutOfRangeException ex)
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
    /// <param name="memorySourceId">The ID of the MemorySource that the document content is linked to</param>
    private async Task ParseDocumentContentToMemoryAsync(IKernel kernel, string content, DocumentImportForm documentImportForm, string memorySourceId)
    {
        var documentName = Path.GetFileName(documentImportForm.FormFile?.FileName);
        var targetCollectionName = documentImportForm.DocumentScope == DocumentImportForm.DocumentScopes.Global
            ? this._options.GlobalDocumentCollectionName
            : this._options.ChatDocumentCollectionNamePrefix + documentImportForm.ChatId;

        // Split the document into lines of text and then combine them into paragraphs.
        // Note that this is only one of many strategies to chunk documents. Feel free to experiment with other strategies.
        var lines = TextChunker.SplitPlainTextLines(content, this._options.DocumentLineSplitMaxTokens);
        var paragraphs = TextChunker.SplitPlainTextParagraphs(lines, this._options.DocumentParagraphSplitMaxLines);

        for (var i = 0; i < paragraphs.Count; i++)
        {
            var paragraph = paragraphs[i];
            await kernel.Memory.SaveInformationAsync(
                collection: targetCollectionName,
                text: paragraph,
                id: $"{memorySourceId}-{i}",
                description: $"Document: {documentName}");
        }

        this._logger.LogInformation(
            "Parsed {0} paragraphs from local file {1}",
            paragraphs.Count,
            documentName
        );
    }

    /// <summary>
    /// Check if the user has access to the chat session.
    /// </summary>
    /// <param name="userId">The user ID.</param>
    /// <param name="chatId">The chat session ID.</param>
    /// <returns>A boolean indicating whether the user has access to the chat session.</returns>
    private async Task<bool> UserHasAccessToChatAsync(string userId, Guid chatId)
    {
        var chatSessions = await this._sessionRepository.FindByUserIdAsync(userId);
        return chatSessions.Any(c => c.Id == chatId.ToString());
    }
}
