// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace GettingStarted.FoundryPromptAgents;

/// <summary>
/// Demonstrate providing image input to a Microsoft Foundry Prompt Agent.
/// </summary>
public class Step03_FoundryPromptAgent_Vision(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    [Fact]
    public async Task UseImageContentWithFoundryPromptAgent()
    {
        // Define the Prompt Agent
        ProjectsAgentVersion promptAgent =
            await this.CreatePromptAgentAsync(
                "Vision",
                new DeclarativeAgentDefinition(DeploymentName));

        // Create the agent
        ChatCompletionAgent agent =
            new()
            {
                Kernel = this.CreateKernel(promptAgent),
            };

        // Load an image
        await using Stream imageStream = EmbeddedResource.ReadStream("cat.jpg")!;
        using MemoryStream imageData = new();
        await imageStream.CopyToAsync(imageData);

        // Respond to user input
        try
        {
            // Refer to public images by url. The service downloads each image, so the url must allow anonymous downloads.
            await InvokeAgentAsync(CreateMessageWithImageUrl("Describe this image.", "https://raw.githubusercontent.com/microsoft/semantic-kernel/main/dotnet/samples/Concepts/Resources/sample_image.jpg"));
            await InvokeAgentAsync(CreateMessageWithImageUrl("What is the main color in this image?", "https://raw.githubusercontent.com/microsoft/semantic-kernel/main/dotnet/samples/Concepts/Resources/test_image.jpg"));
            // Provide the image content.
            await InvokeAgentAsync(CreateMessageWithImageData("Is there an animal in this image?", imageData.ToArray(), "image/jpeg"));
        }
        finally
        {
            await this.DeletePromptAgentAsync(promptAgent);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(ChatMessageContent message)
        {
            this.WriteAgentChatMessage(message);

            // Each image gets its own thread. The thread keeps the conversation locally and sends all of it with every request,
            // so a shared thread would make the service download every earlier image again for each new question.
            AgentThread thread = new ChatHistoryAgentThread();

            await foreach (ChatMessageContent response in agent.InvokeAsync(message, thread))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }

    private ChatMessageContent CreateMessageWithImageUrl(string input, string url)
        => new(AuthorRole.User, [new TextContent(input), new ImageContent(new Uri(url))]);

    private ChatMessageContent CreateMessageWithImageData(string input, byte[] data, string mimeType)
        => new(AuthorRole.User, [new TextContent(input), new ImageContent(data, mimeType)]);
}
