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

        var kernel =
            Kernel.CreateBuilder()
                .AddOpenAIFiles(TestConfiguration.OpenAI.ApiKey)
                .Build();

        var fileService = kernel.GetRequiredService<OpenAIFileService>();
        var fileReference =
            await fileService.UploadContentAsync(
                new BinaryContent(() => Task.FromResult(EmbeddedResource.ReadStream("travelinfo.txt")!)),
                new OpenAIFileUploadExecutionSettings("travelinfo.txt", OpenAIFilePurpose.Assistants));

        WriteLine(fileReference.Id);

        try
        {
            var content = fileService.GetFileContent(fileReference.Id);
            var copyReference = await fileService.GetFileAsync(fileReference.Id);
            Assert.Equal(fileReference.Id, copyReference.Id);
        }
        finally
        {
            await fileService.DeleteFileAsync(fileReference.Id);
        }
    }

    public Example79_OpenAIFiles(ITestOutputHelper output) : base(output) { }
}
