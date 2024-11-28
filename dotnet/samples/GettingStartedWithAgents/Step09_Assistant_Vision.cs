// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace GettingStarted;

/// <summary>
/// Demonstrate providing image input to <see cref="OpenAIAssistantAgent"/> .
/// </summary>
public class Step09_Assistant_Vision(ITestOutputHelper output) : BaseAgentsTest(output)
{
    /// <summary>
    /// Azure currently only supports message of type=text.
    /// </summary>
    protected override bool ForceOpenAI => true;

    [Fact]
    public async Task UseSingleAssistantAgentAsync()
    {
        // Define the agent
        OpenAIClientProvider provider = this.GetClientProvider();
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                provider,
                definition: new OpenAIAssistantDefinition(this.Model)
                {
                    Metadata = AssistantSampleMetadata,
                },
                kernel: new Kernel());

        // Upload an image
        await using Stream imageStream = EmbeddedResource.ReadStream("cat.jpg")!;
        string fileId = await agent.UploadFileAsync(imageStream, "cat.jpg");

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        // Respond to user input
        try
        {
            // Refer to public image by url
            await InvokeAgentAsync(CreateMessageWithImageUrl("Describe this image.", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/New_york_times_square-terabass.jpg/1200px-New_york_times_square-terabass.jpg"));
            await InvokeAgentAsync(CreateMessageWithImageUrl("What are is the main color in this image?", "https://upload.wikimedia.org/wikipedia/commons/5/56/White_shark.jpg"));
            // Refer to uploaded image by file-id.
            await InvokeAgentAsync(CreateMessageWithImageReference("Is there an animal in this image?", fileId));
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
            await provider.Client.GetOpenAIFileClient().DeleteFileAsync(fileId);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(ChatMessageContent message)
        {
            await agent.AddChatMessageAsync(threadId, message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(threadId))
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
