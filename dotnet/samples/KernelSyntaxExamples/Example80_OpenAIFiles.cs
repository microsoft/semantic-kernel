// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Resources;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase usage of Open AI file-service.
/// </summary>
public sealed class Example79_OpenAIFiles : BaseTest
{
    private const string ResourceFileName = "30-user-context.txt";

    /// <summary>
    /// Show how to utilize OpenAI file-service.
    /// </summary>
    [Fact]
    public async Task RunFileLifecycleAsync()
    {
        this.WriteLine("======== OpenAI File-Service ========");

        if (TestConfiguration.OpenAI.ApiKey == null)
        {
            this.WriteLine("OpenAI apiKey not found. Skipping example.");
            return;
        }

        // Initialize file-service
        var kernel =
            Kernel.CreateBuilder()
                .AddOpenAIFiles(TestConfiguration.OpenAI.ApiKey)
                .Build();

        var fileService = kernel.GetRequiredService<OpenAIFileService>();

        // Upload file
        var fileContent = new BinaryContent(() => Task.FromResult(EmbeddedResource.ReadStream(ResourceFileName)!));
        var fileReference =
            await fileService.UploadContentAsync(
                fileContent,
                new OpenAIFileUploadExecutionSettings(ResourceFileName, OpenAIFilePurpose.Assistants));

        WriteLine("SOURCE:");
        WriteLine($"# Name: {fileReference.FileName}");
        WriteLine("# Content:");
        WriteLine(await fileContent.GetContentAsync());

        try
        {
            // Retrieve file metadata for validation.
            var copyReference = await fileService.GetFileAsync(fileReference.Id);
            Assert.Equal(fileReference.Id, copyReference.Id);
            WriteLine("REFERENCE:");
            WriteLine($"# ID: {fileReference.Id}");
            WriteLine($"# Name: {fileReference.FileName}");
            WriteLine($"# Purpose: {fileReference.Purpose}");
        }
        finally
        {
            // Remove file
            await fileService.DeleteFileAsync(fileReference.Id);
        }
    }

    public Example79_OpenAIFiles(ITestOutputHelper output) : base(output) { }
}
