// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.OpenAI.Assistants;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Resources;

namespace Agents;

/// <summary>
/// Demonstrate using retrieval on <see cref="OpenAIAssistantAgent"/> .
/// </summary>
public class OpenAIAssistant_MultipleContents(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Retrieval tool not supported on Azure OpenAI.
    /// </summary>
    protected override bool ForceOpenAI => true;

    [Fact]
    public async Task RunAsync()
    {
        OpenAIFileService fileService = new(TestConfiguration.OpenAI.ApiKey);

        BinaryContent[] files = [
            // Audio is not supported by Assistant API
            // new AudioContent(await EmbeddedResource.ReadAllAsync("test_audio.wav")!, mimeType:"audio/wav", innerContent: "test_audio.wav"),
            new ImageContent(await EmbeddedResource.ReadAllAsync("sample_image.jpg")!, mimeType: "image/jpeg") { InnerContent = "sample_image.jpg" },
            new ImageContent(await EmbeddedResource.ReadAllAsync("test_image.jpg")!, mimeType: "image/jpeg") { InnerContent = "test_image.jpg" },
            new BinaryContent(data: await EmbeddedResource.ReadAllAsync("travelinfo.txt"), mimeType: "text/plain")
            {
                InnerContent = "travelinfo.txt"
            }
        ];

        var fileIds = new List<string>();
        foreach (var file in files)
        {
            try
            {
                var uploadFile = await fileService.UploadContentAsync(file,
                        new OpenAIFileUploadExecutionSettings(file.InnerContent!.ToString()!, Microsoft.SemanticKernel.Connectors.OpenAI.OpenAIFilePurpose.Assistants));

                fileIds.Add(uploadFile.Id);
            }
            catch (HttpOperationException hex)
            {
                Console.WriteLine(hex.ResponseContent);
                Assert.Fail($"Failed to upload file: {hex.Message}");
            }
        }

        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config: new(this.ApiKey, this.Endpoint),
                new()
                {
                    EnableRetrieval = true, // Enable retrieval
                    ModelId = this.Model,
                    // FileIds = fileIds  Currently Assistant API only supports text files, no images or audio.
                    FileIds = [fileIds.Last()]
                });

        // Create a chat for agent interaction.
        var chat = new AgentGroupChat();

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Where did sam go?");
            await InvokeAgentAsync("When does the flight leave Seattle?");
            await InvokeAgentAsync("What is the hotel contact info at the destination?");
        }
        finally
        {
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

            Console.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (var content in chat.InvokeAsync(agent))
            {
                Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
            }
        }
    }

    [Fact]
    public async Task SendingAndRetrievingFilesAsync()
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

            Console.WriteLine($"File: {fileName} - {mimeType}");

            // Images tostring are different from the graduated contents for retrocompatibility
            Console.WriteLine(content.ToString());

            // Delete the test file remotely
            await openAIClient.DeleteFileAsync(file.Id);
        }
    }
}
