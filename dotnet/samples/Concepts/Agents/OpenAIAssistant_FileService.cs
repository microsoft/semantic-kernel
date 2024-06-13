// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.OpenAI.Assistants;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Resources;

namespace Agents;

/// <summary>
/// Demonstrate uploading and retrieving files with <see cref="OpenAIFileService"/> .
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
        var openAIClient = new AssistantsClient(TestConfiguration.OpenAI.ApiKey);
        OpenAIFileService fileService = new(TestConfiguration.OpenAI.ApiKey);

        BinaryContent[] files = [
            new AudioContent(await EmbeddedResource.ReadAllAsync("test_audio.wav")!, mimeType: "audio/wav") { InnerContent = "test_audio.wav" },
            new ImageContent(await EmbeddedResource.ReadAllAsync("sample_image.jpg")!, mimeType: "image/jpeg") { InnerContent = "sample_image.jpg" },
            new ImageContent(await EmbeddedResource.ReadAllAsync("test_image.jpg")!, mimeType: "image/jpeg") { InnerContent = "test_image.jpg" },
            new BinaryContent(data: await EmbeddedResource.ReadAllAsync("travelinfo.txt"), mimeType: "text/plain") { InnerContent = "travelinfo.txt" }
        ];

        var fileIds = new Dictionary<string, BinaryContent>();
        foreach (var file in files)
        {
            var result = await openAIClient.UploadFileAsync(new BinaryData(file.Data), Azure.AI.OpenAI.Assistants.OpenAIFilePurpose.FineTune);
            fileIds.Add(result.Value.Id, file);
        }

        foreach (var file in (await openAIClient.GetFilesAsync(Azure.AI.OpenAI.Assistants.OpenAIFilePurpose.FineTune)).Value)
        {
            if (!fileIds.ContainsKey(file.Id))
            {
                continue;
            }

            var data = (await openAIClient.GetFileContentAsync(file.Id)).Value;

            var mimeType = fileIds[file.Id].MimeType;
            var fileName = fileIds[file.Id].InnerContent!.ToString();
            var metadata = new Dictionary<string, object?> { ["id"] = file.Id };
            var uri = new Uri($"https://api.openai.com/v1/files/{file.Id}/content");
            var content = mimeType switch
            {
                "image/jpeg" => new ImageContent(data, mimeType) { Uri = uri, InnerContent = fileName, Metadata = metadata },
                "audio/wav" => new AudioContent(data, mimeType) { Uri = uri, InnerContent = fileName, Metadata = metadata },
                _ => new BinaryContent(data, mimeType) { Uri = uri, InnerContent = fileName, Metadata = metadata }
            };

            // Display the the file-name and mime-tyupe for each content type.
            Console.WriteLine($"File: {fileName} - {mimeType}");

            // Display the each content type-name.
            Console.WriteLine($"Type: {content}");

            // Delete the test file remotely
            await openAIClient.DeleteFileAsync(file.Id);
        }
    }
}
