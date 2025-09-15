// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to interact with a <see cref="BedrockAgent"/> with code interpreter enabled.
/// </summary>
public class Step02_BedrockAgent_CodeInterpreter(ITestOutputHelper output) : BaseBedrockAgentTest(output)
{
    private const string UserQuery = @"Create a bar chart for the following data:
Panda   5
Tiger   8
Lion    3
Monkey  6
Dolphin  2";

    /// <summary>
    /// Demonstrates how to create a new <see cref="BedrockAgent"/> with code interpreter enabled and interact with it.
    /// The agent will respond to the user query by creating a Python code that will be executed by the code interpreter.
    /// The output of the code interpreter will be a file containing the bar chart, which will be returned to the user.
    /// </summary>
    [Fact]
    public async Task UseAgentWithCodeInterpreter()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step02_BedrockAgent_CodeInterpreter");
        AgentThread bedrockAgentThread = new BedrockAgentThread(this.RuntimeClient);

        // Respond to user input
        try
        {
            BinaryContent? binaryContent = null;
            var responses = bedrockAgent.InvokeAsync(new ChatMessageContent(AuthorRole.User, UserQuery), bedrockAgentThread, null);
            await foreach (ChatMessageContent response in responses)
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
                if (binaryContent == null && response.Items.Count > 0)
                {
                    binaryContent = response.Items.OfType<BinaryContent>().FirstOrDefault();
                }
            }

            if (binaryContent == null)
            {
                throw new InvalidOperationException("No file found in the response.");
            }

            // Save the file to the same directory as the test assembly
            var filePath = Path.Combine(
                Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)!,
                binaryContent.Metadata!["Name"]!.ToString()!);
            this.Output.WriteLine($"Saving file to {filePath}");
            binaryContent.WriteToFile(filePath, overwrite: true);

            // Expected output:
            // Here is the bar chart for the given data:
            // [A bar chart showing the following data:
            // Panda   5
            // Tiger   8
            // Lion    3
            // Monkey  6
            // Dolphin 2]
            // Saving file to ...
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
            await bedrockAgentThread.DeleteAsync();
        }
    }

    protected override async Task<BedrockAgent> CreateAgentAsync(string agentName)
    {
        // Create a new agent on the Bedrock Agent service and prepare it for use
        var agentModel = await this.Client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest(agentName));
        // Create a new BedrockAgent instance with the agent model and the client
        // so that we can interact with the agent using Semantic Kernel contents.
        var bedrockAgent = new BedrockAgent(agentModel, this.Client, this.RuntimeClient);
        // Create the code interpreter action group and prepare the agent for interaction
        await bedrockAgent.CreateCodeInterpreterActionGroupAsync();

        return bedrockAgent;
    }
}
