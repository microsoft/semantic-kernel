// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Bedrock;

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
    public async Task UseAgentWithCodeInterpreterAsync()
    {
        // Create the agent
        var bedrock_agent = await this.CreateAgentAsync("Step02_BedrockAgent_CodeInterpreter");

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
            await bedrock_agent.DeleteAsync(CancellationToken.None);
        }
    }

    protected override async Task<BedrockAgent> CreateAgentAsync(string agentName)
    {
        return await BedrockAgent.CreateAsync(this.GetCreateAgentRequest(agentName), enableCodeInterpreter: true);
    }
}
