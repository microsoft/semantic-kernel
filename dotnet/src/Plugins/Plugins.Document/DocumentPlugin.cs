// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
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
/// Plugin for interacting with documents (e.g. Microsoft Word)
/// </summary>
/// <remarks>
/// <para>
/// This plugin is secure by default. <see cref="AllowedDirectories"/> must be explicitly configured
/// before any file operations are permitted. By default, all file paths are denied.
/// </para>
/// <para>
/// When exposing this plugin to an LLM via auto function calling, ensure that
/// <see cref="AllowedDirectories"/> is restricted to trusted values only.
/// </para>
/// </remarks>
public sealed class DocumentPlugin
{
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
        this._logger = loggerFactory?.CreateLogger(typeof(DocumentPlugin)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// List of allowed directories for file operations. Subdirectories of allowed directories are also permitted.
    /// </summary>
    /// <remarks>
    /// Defaults to an empty collection (no directories allowed). Must be explicitly populated
    /// with trusted directory paths before any file operations will succeed.
    /// Paths are canonicalized before validation to prevent directory traversal.
    /// </remarks>
    public IEnumerable<string>? AllowedDirectories
    {
        get => this._allowedDirectories;
        set => this._allowedDirectories = value is null ? null : new HashSet<string>(value, StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Read all text from a document, using the filePath argument as the file path.
    /// </summary>
    [KernelFunction, Description("Read all text from a document")]
    public async Task<string> ReadTextAsync(
        [Description("Path to the file to read")] string filePath,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Reading text from {0}", filePath);

        if (!this.IsFilePathAllowed(filePath))
        {
            throw new InvalidOperationException("Reading from the provided location is not allowed.");
        }

        using var stream = await this._fileSystemConnector.GetFileContentStreamAsync(filePath, cancellationToken).ConfigureAwait(false);
        return this._documentConnector.ReadText(stream);
    }

    /// <summary>
    /// Append the text specified by the text argument to a document. If the document doesn't exist, it will be created.
    /// </summary>
    [KernelFunction, Description("Append text to a document. If the document doesn't exist, it will be created.")]
    public async Task AppendTextAsync(
        [Description("Text to append")] string text,
        [Description("Destination file path")] string filePath,
        CancellationToken cancellationToken = default)
    {
        if (!this.IsFilePathAllowed(filePath))
        {
            throw new InvalidOperationException("Writing to the provided location is not allowed.");
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

    #region private
    private HashSet<string>? _allowedDirectories = [];

    /// <summary>
    /// If a list of allowed directories has been provided, the directory of the provided filePath is checked
    /// to verify it is in the allowed directory list. Paths are canonicalized before comparison.
    /// Subdirectories of allowed directories are also permitted.
    /// </summary>
    private bool IsFilePathAllowed(string path)
    {
        Verify.NotNullOrWhiteSpace(path);

        if (path.StartsWith("\\\\", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("Invalid file path, UNC paths are not supported.", nameof(path));
        }

        string? directoryPath = Path.GetDirectoryName(path);

        if (string.IsNullOrEmpty(directoryPath))
        {
            throw new ArgumentException("Invalid file path, a fully qualified file location must be specified.", nameof(path));
        }

        if (this._allowedDirectories is null || this._allowedDirectories.Count == 0)
        {
            return false;
        }

        var canonicalDir = Path.GetFullPath(directoryPath);

        foreach (var allowedDirectory in this._allowedDirectories)
        {
            var canonicalAllowed = Path.GetFullPath(allowedDirectory);
            var separator = Path.DirectorySeparatorChar.ToString();
            if (!canonicalAllowed.EndsWith(separator, StringComparison.OrdinalIgnoreCase))
            {
                canonicalAllowed += separator;
            }

            if (canonicalDir.StartsWith(canonicalAllowed, StringComparison.OrdinalIgnoreCase)
                || (canonicalDir + separator).Equals(canonicalAllowed, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return false;
    }
    #endregion
}
