// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Agents.Persistent;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace GettingStarted.AzureAgents;

/// <summary>
/// Demonstrate using code-interpreter on <see cref="AzureAIAgent"/> .
/// </summary>
public class Step03_AzureAIAgent_Vision(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    [Fact]
    public async Task UseImageContentWithAgent()
    {
        // Upload an image
        await using Stream imageStream = EmbeddedResource.ReadStream("cat.jpg")!;
        PersistentAgentFileInfo fileInfo = await this.Client.Files.UploadFileAsync(imageStream, PersistentAgentFilePurpose.Agents, "cat.jpg");

        // Define the agent
        PersistentAgent definition = await this.Client.Administration.CreateAgentAsync(TestConfiguration.AzureAI.ChatModelId);
        AzureAIAgent agent = new(definition, this.Client);

        // Create a thread for the agent conversation.
        AzureAIAgentThread thread = new(this.Client, metadata: SampleMetadata);

        // Respond to user input
        try
        {
            // Refer to public image by url
            await InvokeAgentAsync(CreateMessageWithImageUrl("Describe this image.", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/New_york_times_square-terabass.jpg/1200px-New_york_times_square-terabass.jpg"));
            await InvokeAgentAsync(CreateMessageWithImageUrl("What are is the main color in this image?", "https://upload.wikimedia.org/wikipedia/commons/5/56/White_shark.jpg"));
            // Refer to uploaded image by file-id.
            await InvokeAgentAsync(CreateMessageWithImageReference("Is there an animal in this image?", fileInfo.Id));
        }
        finally
        {
            await thread.DeleteAsync();
            await this.Client.Administration.DeleteAgentAsync(agent.Id);
            await this.Client.Files.DeleteFileAsync(fileInfo.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(ChatMessageContent input)
        {
            this.WriteAgentChatMessage(input);

            await foreach (ChatMessageContent response in agent.InvokeAsync(input, thread))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }

    private ChatMessageContent CreateMessageWithImageUrl(string input, string url)
        => new(AuthorRole.User, [new TextContent(input), new ImageContent(new Uri(url))]);

    private ChatMessageContent CreateMessageWithImageReference(string input, string fileId)
        => new(AuthorRole.User, [new TextContent(input), new FileReferenceContent(fileId)]);
}
