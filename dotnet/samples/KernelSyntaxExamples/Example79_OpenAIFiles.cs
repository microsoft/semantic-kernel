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
        var fileReference =
            await fileService.UploadContentAsync(
                new BinaryContent(() => Task.FromResult(EmbeddedResource.ReadStream(ResourceFileName)!)),
                new OpenAIFileUploadExecutionSettings(ResourceFileName, OpenAIFilePurpose.Assistants));

        WriteLine($"# {fileReference.Id}");

        try
        {
            // Retrieve file content
            var content = fileService.GetFileContent(fileReference.Id);
            WriteLine($"# Content:");
            WriteLine(content);

            // Retrieve file metadata (again)
            var copyReference = await fileService.GetFileAsync(fileReference.Id);
            Assert.Equal(fileReference.Id, copyReference.Id);
        }
        finally
        {
            // Remove file
            await fileService.DeleteFileAsync(fileReference.Id);
        }
    }

    public Example79_OpenAIFiles(ITestOutputHelper output) : base(output) { }
}
