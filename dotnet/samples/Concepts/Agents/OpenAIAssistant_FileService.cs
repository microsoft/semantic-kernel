// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Resources;

namespace Agents;

/// <summary>
/// Demonstrate using <see cref="OpenAIFileService"/> .
/// </summary>
public class OpenAIAssistant_FileService(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Retrieval tool not supported on Azure OpenAI.
    /// </summary>
    protected override bool ForceOpenAI => true;

    [Fact]
    public async Task UploadAndRetrieveFilesAsync()
    {
        OpenAIFileService fileService = new(TestConfiguration.OpenAI.ApiKey);

        BinaryContent[] files = [
            new AudioContent(await EmbeddedResource.ReadAllAsync("test_audio.wav")!, mimeType: "audio/wav") { InnerContent = "test_audio.wav" },
            new ImageContent(await EmbeddedResource.ReadAllAsync("sample_image.jpg")!, mimeType: "image/jpeg") { InnerContent = "sample_image.jpg" },
            new ImageContent(await EmbeddedResource.ReadAllAsync("test_image.jpg")!, mimeType: "image/jpeg") { InnerContent = "test_image.jpg" },
            new BinaryContent(data: await EmbeddedResource.ReadAllAsync("travelinfo.txt"), mimeType: "text/plain") { InnerContent = "travelinfo.txt" }
        ];

        var fileContents = new Dictionary<string, BinaryContent>();
        foreach (BinaryContent file in files)
        {
            OpenAIFileReference result = await fileService.UploadContentAsync(file, new(file.InnerContent!.ToString()!, OpenAIFilePurpose.FineTune));
            fileContents.Add(result.Id, file);
        }

        foreach (OpenAIFileReference fileReference in await fileService.GetFilesAsync(OpenAIFilePurpose.FineTune))
        {
            // Only interested in the files we uploaded
            if (!fileContents.ContainsKey(fileReference.Id))
            {
                continue;
            }

            BinaryContent content = await fileService.GetFileContentAsync(fileReference.Id);

            string? mimeType = fileContents[fileReference.Id].MimeType;
            string? fileName = fileContents[fileReference.Id].InnerContent!.ToString();
            ReadOnlyMemory<byte> data = content.Data ?? new();

            var typedContent = mimeType switch
            {
                "image/jpeg" => new ImageContent(data, mimeType) { Uri = content.Uri, InnerContent = fileName, Metadata = content.Metadata },
                "audio/wav" => new AudioContent(data, mimeType) { Uri = content.Uri, InnerContent = fileName, Metadata = content.Metadata },
                _ => new BinaryContent(data, mimeType) { Uri = content.Uri, InnerContent = fileName, Metadata = content.Metadata }
            };

            Console.WriteLine($"\nFile: {fileName} - {mimeType}");
            Console.WriteLine($"Type: {typedContent}");
            Console.WriteLine($"Uri: {typedContent.Uri}");

            // Delete the test file remotely
            await fileService.DeleteFileAsync(fileReference.Id);
        }
    }
}
