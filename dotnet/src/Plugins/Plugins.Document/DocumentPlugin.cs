// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Plugins.Document.FileSystem;

namespace Microsoft.SemanticKernel.Plugins.Document;

//**********************************************************************************************************************
// EXAMPLE USAGE
// Option #1: as a standalone C# function
//
// DocumentPlugin documentPlugin = new(new WordDocumentConnector(), new LocalDriveConnector());
// string filePath = "PATH_TO_DOCX_FILE.docx";
// string text = await documentPlugin.ReadTextAsync(filePath);
// Console.WriteLine(text);
//
//
// Option #2: with the Semantic Kernel
//
// DocumentPlugin documentPlugin = new(new WordDocumentConnector(), new LocalDriveConnector());
// string filePath = "PATH_TO_DOCX_FILE.docx";
// ISemanticKernel kernel = SemanticKernel.Build();
// var result = await kernel.RunAsync(
//      filePath,
//      documentPlugin.ReadTextAsync);
// Console.WriteLine(result);
//**********************************************************************************************************************

/// <summary>
/// Skill for interacting with documents (e.g. Microsoft Word)
/// </summary>
public sealed class DocumentPlugin
{
    /// <summary>
    /// <see cref="ContextVariables"/> parameter names.
    /// </summary>
    public static class Parameters
    {
        /// <summary>
        /// Document file path.
        /// </summary>
        public const string FilePath = "filePath";
    }

    private readonly IDocumentConnector _documentConnector;
    private readonly IFileSystemConnector _fileSystemConnector;
    private readonly ILogger _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="DocumentPlugin"/> class.
    /// </summary>
    /// <param name="documentConnector">Document connector</param>
    /// <param name="fileSystemConnector">File system connector</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public DocumentPlugin(IDocumentConnector documentConnector, IFileSystemConnector fileSystemConnector, ILoggerFactory? loggerFactory = null)
    {
        this._documentConnector = documentConnector ?? throw new ArgumentNullException(nameof(documentConnector));
        this._fileSystemConnector = fileSystemConnector ?? throw new ArgumentNullException(nameof(fileSystemConnector));
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(DocumentPlugin)) : NullLogger.Instance;
    }

    /// <summary>
    /// Read all text from a document, using <see cref="ContextVariables.Input"/> as the file path.
    /// </summary>
    [SKFunction, Description("Read all text from a document")]
    public async Task<string> ReadTextAsync(
        [Description("Path to the file to read")] string filePath,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Reading text from {0}", filePath);
        using var stream = await this._fileSystemConnector.GetFileContentStreamAsync(filePath, cancellationToken).ConfigureAwait(false);
        return this._documentConnector.ReadText(stream);
    }

    /// <summary>
    /// Append the text in <see cref="ContextVariables.Input"/> to a document. If the document doesn't exist, it will be created.
    /// </summary>
    [SKFunction, Description("Append text to a document. If the document doesn't exist, it will be created.")]
    public async Task AppendTextAsync(
        [Description("Text to append")] string text,
        [Description("Destination file path")] string filePath,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(filePath))
        {
            throw new ArgumentException("Variable was null or whitespace", nameof(filePath));
        }

        // If the document already exists, open it. If not, create it.
        if (await this._fileSystemConnector.FileExistsAsync(filePath, cancellationToken).ConfigureAwait(false))
        {
            this._logger.LogDebug("Writing text to file {0}", filePath);
            using Stream stream = await this._fileSystemConnector.GetWriteableFileStreamAsync(filePath, cancellationToken).ConfigureAwait(false);
            this._documentConnector.AppendText(stream, text);
        }
        else
        {
            this._logger.LogDebug("File does not exist. Creating file at {0}", filePath);
            using Stream stream = await this._fileSystemConnector.CreateFileAsync(filePath, cancellationToken).ConfigureAwait(false);
            this._documentConnector.Initialize(stream);

            this._logger.LogDebug("Writing text to {0}", filePath);
            this._documentConnector.AppendText(stream, text);
        }
    }
}
