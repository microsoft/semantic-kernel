// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Amazon.BedrockAgent.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Bedrock;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to interact with a <see cref="BedrockAgent"/> with code interpreter enabled.
/// </summary>
public class Step02_BedrockAgent_CodeInterpreter(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private const string AgentName = "Semantic-Kernel-Test-Agent";
    private const string AgentDescription = "A helpful assistant who helps users find information.";
    private const string AgentInstruction = "You're a helpful assistant who helps users find information.";
    private const string UserQuery = @"Create a bar chart for the following data:
Panda   5
Tiger   8
Lion    3
Monkey  6
Dolphin  2";

    [Fact]
    public async Task UseAgentWithCodeInterpreterAsync()
    {
        // Define the agent
        CreateAgentRequest createAgentRequest = new()
        {
            AgentName = AgentName,
            Description = AgentDescription,
            Instruction = AgentInstruction,
            AgentResourceRoleArn = TestConfiguration.BedrockAgent.AgentResourceRoleArn,
            FoundationModel = TestConfiguration.BedrockAgent.FoundationModel,
        };

        var bedrock_agent = await BedrockAgent.CreateAsync(createAgentRequest, enableCodeInterpreter: true);

        // Respond to user input
        try
        {
            BinaryContent? binaryContent = null;
            var responses = bedrock_agent.InvokeAsync(BedrockAgent.CreateSessionId(), UserQuery, null, CancellationToken.None);
            await foreach (var response in responses)
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
                if (binaryContent == null && response.Items.Count > 0 && response.Items[0] is BinaryContent binary)
                {
                    binaryContent = binary;
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
            binaryContent.WriteToFile(filePath);

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
            await bedrock_agent.DeleteAsync(CancellationToken.None);
        }
    }
}
