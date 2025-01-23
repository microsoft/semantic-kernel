// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;
using AzureAIP = Azure.AI.Projects;

namespace GettingStarted;

/// <summary>
/// Demonstrate providing image input to <see cref="AzureAIAgent"/> .
/// </summary>
public class Step14_Azure_Vision(ITestOutputHelper output) : BaseAgentsTest(output)
{
    /// <summary>
    /// Azure currently only supports message of type=text.
    /// </summary>
    protected override bool ForceOpenAI => true;

    [Fact]
    public async Task UseSingleAssistantAgentAsync()
    {
        // Define the agent
        AzureAIClientProvider clientProvider = this.GetAzureProvider();
        AzureAIP.AgentsClient client = clientProvider.Client.GetAgentsClient();
        AzureAIP.Agent definition = await client.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId);
        AzureAIAgent agent = new(definition, clientProvider)
        {
            Kernel = new Kernel(),
        };

        // Upload an image
        await using Stream imageStream = EmbeddedResource.ReadStream("cat.jpg")!;
        AzureAIP.AgentFile fileInfo = await client.UploadFileAsync(imageStream, AzureAIP.AgentFilePurpose.Agents, "cat.jpg");

        // Create a thread for the agent conversation.
        AgentThread thread = await client.CreateThreadAsync(metadata: AssistantSampleMetadata);

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
            await client.DeleteThreadAsync(thread.Id);
            await client.DeleteAgentAsync(agent.Id);
            await client.DeleteFileAsync(fileInfo.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(ChatMessageContent message)
        {
            await agent.AddChatMessageAsync(thread.Id, message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(thread.Id))
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
