// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.Document.FileSystem;

namespace Microsoft.SemanticKernel.Skills.Document;

//**********************************************************************************************************************
// EXAMPLE USAGE
// Option #1: as a standalone C# function
//
// DocumentSkill documentSkill = new(new WordDocumentAdapter(), new LocalDriveAdapter());
// string filePath = "PATH_TO_DOCX_FILE.docx";
// string text = await documentSkill.ReadTextAsync(filePath);
// Console.WriteLine(text);
//
//
// Option #2: with the Semantic Kernel
//
// DocumentSkill documentSkill = new(new WordDocumentAdapter(), new LocalDriveAdapter());
// string filePath = "PATH_TO_DOCX_FILE.docx";
// ISemanticKernel kernel = SemanticKernel.Build();
// var result = await kernel.RunAsync(
//      filePath,
//      documentSkill.ReadTextAsync);
// Console.WriteLine(result);
//**********************************************************************************************************************

/// <summary>
/// Skill for interacting with documents (e.g. Microsoft Word)
/// </summary>
public class DocumentSkill
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

    private readonly IDocumentAdapter _documentAdapter;
    private readonly IFileSystemAdapter _fileSystemAdapter;
    private readonly ILogger<DocumentSkill> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="DocumentSkill"/> class.
    /// </summary>
    /// <param name="documentAdapter">Document adapter</param>
    /// <param name="fileSystemAdapter">File system adapter</param>
    /// <param name="logger">Optional logger</param>
    public DocumentSkill(IDocumentAdapter documentAdapter, IFileSystemAdapter fileSystemAdapter, ILogger<DocumentSkill>? logger = null)
    {
        this._documentAdapter = documentAdapter ?? throw new ArgumentNullException(nameof(documentAdapter));
        this._fileSystemAdapter = fileSystemAdapter ?? throw new ArgumentNullException(nameof(fileSystemAdapter));
        this._logger = logger ?? new NullLogger<DocumentSkill>();
    }

    /// <summary>
    /// Read all text from a document, using <see cref="ContextVariables.Input"/> as the file path.
    /// </summary>
    [SKFunction("Read all text from a document")]
    [SKFunctionInput(Description = "Path to the file to read")]
    public async Task<string> ReadTextAsync(string filePath, SKContext context)
    {
        this._logger.LogInformation("Reading text from {0}", filePath);
        using var stream = await this._fileSystemAdapter.GetFileContentStreamAsync(filePath, context.CancellationToken).ConfigureAwait(false);
        return this._documentAdapter.ReadText(stream);
    }

    /// <summary>
    /// Append the text in <see cref="ContextVariables.Input"/> to a document. If the document doesn't exist, it will be created.
    /// </summary>
    [SKFunction("Append text to a document. If the document doesn't exist, it will be created.")]
    [SKFunctionInput(Description = "Text to append")]
    [SKFunctionContextParameter(Name = Parameters.FilePath, Description = "Destination file path")]
    public async Task AppendTextAsync(string text, SKContext context)
    {
        if (!context.Variables.Get(Parameters.FilePath, out string filePath))
        {
            context.Fail($"Missing variable {Parameters.FilePath}.");
            return;
        }

        // If the document already exists, open it. If not, create it.
        if (await this._fileSystemAdapter.FileExistsAsync(filePath).ConfigureAwait(false))
        {
            this._logger.LogInformation("Writing text to file {0}", filePath);
            using Stream stream = await this._fileSystemAdapter.GetWriteableFileStreamAsync(filePath, context.CancellationToken).ConfigureAwait(false);
            this._documentAdapter.AppendText(stream, text);
        }
        else
        {
            this._logger.LogInformation("File does not exist. Creating file at {0}", filePath);
            using Stream stream = await this._fileSystemAdapter.CreateFileAsync(filePath).ConfigureAwait(false);
            this._documentAdapter.Initialize(stream);

            this._logger.LogInformation("Writing text to {0}", filePath);
            this._documentAdapter.AppendText(stream, text);
        }
    }
}
