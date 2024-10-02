// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted;

/// <summary>
/// Demonstrate using code-interpreter on <see cref="OpenAIAssistantAgent"/> .
/// </summary>
public class Step10_AssistantTool_CodeInterpreter(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseCodeInterpreterToolWithAssistantAgentAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                clientProvider: this.GetClientProvider(),
                definition: new(this.Model)
                {
                    EnableCodeInterpreter = true,
                    Metadata = AssistantSampleMetadata,
                },
                kernel: new Kernel());

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Use code to determine the values in the Fibonacci sequence that that are less then the value of 101?");
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            await agent.AddChatMessageAsync(threadId, message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(threadId))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
}
