// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.Compression;
using Microsoft.SemanticKernel.Skills.Web;
using Xunit;
using Xunit.Abstractions;

namespace IntegrationTests.Compression;

public class CompressionTests : IDisposable
{
    public CompressionTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<Kernel>(output);
        this._output = output;

        this._testOutputHelper = new RedirectOutput(output);
        Console.SetOut(this._testOutputHelper);
    }

    [Fact]
    public async Task ZipFileCompressionAndDecompressionTestAsync()
    {
        // Arrange
        IKernel kernel = Kernel.Builder.WithLogger(this._logger).Build();
        using XunitLogger<WebFileDownloadSkill> skillLogger = new(this._output);
        var zipCompressor = new ZipFileCompressor();
        var skill = new FileCompressionSkill(zipCompressor);
        var fileCompression = kernel.ImportSkill(skill, "FileCompression");

        string tempPath = Path.GetTempPath();
        string tempFileName = Path.GetRandomFileName();
        var sourceFilePath = Path.Join(tempPath, tempFileName);
        var destinationFilePath = sourceFilePath + ".zip";
        await File.WriteAllTextAsync(sourceFilePath, new string('*', 100));

        var contextVariables = new ContextVariables(sourceFilePath);
        contextVariables.Set(FileCompressionSkill.Parameters.DestinationFilePath, destinationFilePath);

        // Act
        await kernel.RunAsync(contextVariables, fileCompression["CompressFileAsync"]);
        string uncompressedFilePath = sourceFilePath + ".original";
        File.Move(sourceFilePath, uncompressedFilePath);
        contextVariables = new ContextVariables(destinationFilePath);
        contextVariables.Set(FileCompressionSkill.Parameters.DestinationDirectoryPath, tempPath);
        await kernel.RunAsync(contextVariables, fileCompression["DecompressFileAsync"]);

        // Assert
        string uncompressedFileContents = await File.ReadAllTextAsync(uncompressedFilePath);
        string decompressedFilePath = sourceFilePath;
        string decompressedFileContents = await File.ReadAllTextAsync(decompressedFilePath);
        Assert.Equal(uncompressedFileContents, decompressedFileContents);
    }

    [Fact]
    public async Task ZipDirectoryCompressionAndDecompressionTestAsync()
    {
        // Arrange
        var zipCompressor = new ZipFileCompressor();
        var sourceFilePath = "C:\\temp\\test.txt";
        var destinationFilePath = "C:\\temp\\test.zip";

        // Act
        await zipCompressor.CompressFileAsync(sourceFilePath, destinationFilePath, CancellationToken.None);

        // Assert
        Assert.True(File.Exists(destinationFilePath));
    }

    private readonly XunitLogger<Kernel> _logger;
    private readonly ITestOutputHelper _output;
    private readonly RedirectOutput _testOutputHelper;

    /// <summary>
    /// Implementation of IDisposable.
    /// </summary>
    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Code that does the actual disposal of resources.
    /// </summary>
    /// <param name="disposing">Dispose of resources only if this is true.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._logger.Dispose();
            this._testOutputHelper.Dispose();
        }
    }
}
