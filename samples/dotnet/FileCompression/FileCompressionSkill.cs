// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace FileCompression;

/// <summary>
/// Skill for compressing and decompressing files.
/// </summary>
/// <example>
/// ISemanticKernel kernel = SemanticKernel.Build();
/// var zipCompressor = new ZipFileCompressor();
/// var skill = new FileCompressionSkill(zipCompressor);
/// var fileCompression = kernel.ImportSkill(skill, "FileCompression");
/// string sourceFilePath = "FileToCompress.txt";
/// string destinationFilePath = "CompressedFile.zip";
/// var variables = new ContextVariables(sourceFilePath);
/// variables.Set(FileCompressionSkill.Parameters.DestinationFilePath, destinationFilePath);
/// await kernel.RunAsync(variables, fileCompression["CompressFileAsync"]);
/// </example>
public class FileCompressionSkill
{
    /// <summary>
    /// Parameter names.
    /// <see cref="ContextVariables"/>
    /// </summary>
    public static class Parameters
    {
        /// <summary>
        /// Directory to which to extract compressed file's data.
        /// </summary>
        public const string DestinationDirectoryPath = "destinationDirectoryPath";

        /// <summary>
        /// File path where to save compressed data.
        /// </summary>
        public const string DestinationFilePath = "destinationFilePath";
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FileCompressionSkill"/> class.
    /// </summary>
    /// <param name="fileCompressor">File compressor implementation</param>
    /// <param name="logger">Optional logger</param>
    public FileCompressionSkill(IFileCompressor fileCompressor, ILogger<FileCompressionSkill>? logger = null)
    {
        this._fileCompressor = fileCompressor ?? throw new ArgumentNullException(nameof(fileCompressor));
        this._logger = logger ?? new NullLogger<FileCompressionSkill>();
    }

    /// <summary>
    /// Compresses an input file to an output file.
    /// </summary>
    /// <param name="sourceFilePath">Path of file to compress</param>
    /// <param name="context">Semantic Kernel context</param>
    /// <returns>Path of created compressed file</returns>
    /// <exception cref="KeyNotFoundException"></exception>
    [SKFunction("Compresses an input file to an output file")]
    [SKFunctionInput(Description = "Path of file to compress")]
    [SKFunctionContextParameter(Name = Parameters.DestinationFilePath, Description = "Path of compressed file to create")]
    public async Task<string?> CompressFileAsync(string sourceFilePath, SKContext context)
    {
        this._logger.LogTrace($"{nameof(this.CompressFileAsync)} got called");

        if (!context.Variables.TryGetValue(Parameters.DestinationFilePath, out string? destinationFilePath))
        {
            const string ErrorMessage = $"Missing context variable {Parameters.DestinationFilePath} in {nameof(this.CompressFileAsync)}";
            this._logger.LogError(ErrorMessage);
            context.Fail(ErrorMessage);

            return null;
        }

        await this._fileCompressor.CompressFileAsync(Environment.ExpandEnvironmentVariables(sourceFilePath),
            Environment.ExpandEnvironmentVariables(destinationFilePath),
            context.CancellationToken);

        return destinationFilePath;
    }

    /// <summary>
    /// Compresses a directory to an output file.
    /// </summary>
    /// <param name="sourceDirectoryPath">Path of directory to compress</param>
    /// <param name="context">Semantic Kernel context</param>
    /// <returns>Path of created compressed file</returns>
    /// <exception cref="KeyNotFoundException"></exception>
    [SKFunction("Compresses a directory to an output file")]
    [SKFunctionInput(Description = "Path of directory to compress")]
    [SKFunctionContextParameter(Name = Parameters.DestinationFilePath, Description = "Path of compressed file to create")]
    public async Task<string?> CompressDirectoryAsync(string sourceDirectoryPath, SKContext context)
    {
        this._logger.LogTrace($"{nameof(this.CompressDirectoryAsync)} got called");

        if (!context.Variables.TryGetValue(Parameters.DestinationFilePath, out string? destinationFilePath))
        {
            const string ErrorMessage = $"Missing context variable {Parameters.DestinationFilePath} in {nameof(this.CompressDirectoryAsync)}";
            this._logger.LogError(ErrorMessage);
            context.Fail(ErrorMessage);

            return null;
        }

        await this._fileCompressor.CompressDirectoryAsync(Environment.ExpandEnvironmentVariables(sourceDirectoryPath),
            Environment.ExpandEnvironmentVariables(destinationFilePath),
            context.CancellationToken);

        return destinationFilePath;
    }

    /// <summary>
    /// Decompresses an input file.
    /// </summary>
    /// <param name="sourceFilePath">Path of file to decompress</param>
    /// <param name="context">Semantic Kernel context</param>
    /// <returns>Path of created compressed file</returns>
    /// <exception cref="KeyNotFoundException"></exception>
    [SKFunction("Decompresses an input file")]
    [SKFunctionInput(Description = "Path of directory into which decompressed content was extracted")]
    [SKFunctionContextParameter(Name = Parameters.DestinationDirectoryPath, Description = "Directory into which to extract the decompressed content")]
    public async Task<string?> DecompressFileAsync(string sourceFilePath, SKContext context)
    {
        this._logger.LogTrace($"{nameof(this.DecompressFileAsync)} got called");

        if (!context.Variables.TryGetValue(Parameters.DestinationDirectoryPath, out string? destinationDirectoryPath))
        {
            const string ErrorMessage = $"Missing context variable {Parameters.DestinationDirectoryPath} in {nameof(this.DecompressFileAsync)}";
            this._logger.LogError(ErrorMessage);
            context.Fail(ErrorMessage);

            return null;
        }

        if (!Directory.Exists(destinationDirectoryPath))
        {
            Directory.CreateDirectory(destinationDirectoryPath);
        }

        await this._fileCompressor.DecompressFileAsync(Environment.ExpandEnvironmentVariables(sourceFilePath),
            Environment.ExpandEnvironmentVariables(destinationDirectoryPath),
            context.CancellationToken);

        return destinationDirectoryPath;
    }

    private readonly IFileCompressor _fileCompressor;
    private readonly ILogger<FileCompressionSkill> _logger;
}
