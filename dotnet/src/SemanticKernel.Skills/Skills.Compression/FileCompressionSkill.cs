// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Skills.Compression;

//**********************************************************************************************************************
// EXAMPLE USAGE
//
// CompressionSkill compressionSkill = new(new ZipCompressionConnector());
// string sourceFilePath = "FileToCompress.txt";
// string destinationFilePath = "CompressedFile.zip";
// ISemanticKernel kernel = SemanticKernel.Build();
// var variables = new ContextVariables(sourceFilePath);
// variables.Set(FileCompressionSkill.Parameters.DestinationFilePath, destinationFilePath);
// await kernel.RunAsync(variables, compressionSkill.CompressFileAsync);
//**********************************************************************************************************************

/// <summary>
/// Skill for compressing and decompressing files.
/// </summary>
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

    private readonly IFileCompressor _fileCompressor;
    private readonly ILogger<FileCompressionSkill> _logger;

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

    [SKFunction("Compresses an input file to an output file")]
    [SKFunctionInput(Description = "Path of file to compress")]
    [SKFunctionContextParameter(Name = Parameters.DestinationFilePath, Description = "Path of compressed file to create")]
    public Task CompressFileAsync(string sourceFilePath, SKContext context)
    {
        this._logger.LogDebug($"{nameof(CompressFileAsync)} got called");

        if (!context.Variables.Get(Parameters.DestinationFilePath, out string destinationFilePath))
        {
            this._logger.LogError($"Missing context variable in {nameof(CompressFileAsync)}");
            string errorMessage = $"Missing variable {Parameters.DestinationFilePath}";
            context.Fail(errorMessage);

            return Task.FromException(new KeyNotFoundException(errorMessage));
        }

        return this._fileCompressor.CompressFileAsync(sourceFilePath, destinationFilePath, context.CancellationToken);
    }

    [SKFunction("Compresses a directory to an output file")]
    [SKFunctionInput(Description = "Path of directory to compress")]
    [SKFunctionContextParameter(Name = Parameters.DestinationFilePath, Description = "Path of compressed file to create")]
    public Task CompressDirectoryAsync(string sourceDirectoryPath, SKContext context)
    {
        this._logger.LogDebug($"{nameof(CompressDirectoryAsync)} got called");

        if (!context.Variables.Get(Parameters.DestinationFilePath, out string destinationFilePath))
        {
            this._logger.LogError($"Missing context variable in {nameof(CompressDirectoryAsync)}");
            string errorMessage = $"Missing variable {Parameters.DestinationFilePath}";
            context.Fail(errorMessage);

            return Task.FromException(new KeyNotFoundException(errorMessage));
        }

        return this._fileCompressor.CompressDirectoryAsync(sourceDirectoryPath, destinationFilePath, context.CancellationToken);
    }

    [SKFunction("Decompresses an input file")]
    [SKFunctionInput(Description = "Path of file to decompress")]
    [SKFunctionContextParameter(Name = Parameters.DestinationDirectoryPath, Description = "Directory into which to extract the decompressed content")]
    public Task DecompressFileAsync(string sourceFilePath, SKContext context)
    {
        this._logger.LogDebug($"{nameof(DecompressFileAsync)} got called");

        if (!context.Variables.Get(Parameters.DestinationDirectoryPath, out string destinationDirectoryPath))
        {
            this._logger.LogError($"Missing context variable in {nameof(DecompressFileAsync)}");
            string errorMessage = $"Missing variable {Parameters.DestinationDirectoryPath}";
            context.Fail(errorMessage);

            return Task.FromException(new KeyNotFoundException(errorMessage));
        }

        return this._fileCompressor.DecompressFileAsync(sourceFilePath, destinationDirectoryPath, context.CancellationToken);
    }
}
