// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI.Responses;

namespace GettingStarted.OpenAIResponseAgents;

/// <summary>
/// This example demonstrates using <see cref="OpenAIResponseAgent"/>.
/// </summary>
public class Step03_OpenAIResponseAgent_ReasoningModel(ITestOutputHelper output) : BaseResponsesAgentTest(output, "o4-mini")
{
    [Fact]
    public async Task UseOpenAIResponseAgentWithAReasoningModelAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer all queries with a detailed response.",
        };

        // Invoke the agent and output the response
        var responseItems = agent.InvokeAsync("Which of the last four Olympic host cities has the highest average temperature?");
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            WriteAgentChatMessage(responseItem);
        }
    }

    [Fact]
    public async Task UseOpenAIResponseAgentWithAReasoningModelAndSummariesAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Explain your responses.",
        };

        // ResponseCreationOptions allows you to specify tools for the agent.
        OpenAIResponseAgentInvokeOptions invokeOptions = new()
        {
            ResponseCreationOptions = new()
            {
                ReasoningOptions = new()
                {
                    ReasoningEffortLevel = ResponseReasoningEffortLevel.High,
                    // This parameter cannot be used due to a known issue in the OpenAI .NET SDK.
                    // https://github.com/openai/openai-dotnet/issues/457
                    // ReasoningSummaryVerbosity = ResponseReasoningSummaryVerbosity.Detailed,
                },
            },
        };

        // Invoke the agent and output the response
        var responseItems = agent.InvokeAsync(
            """
            Instructions:
            - Given the React component below, change it so that nonfiction books have red
              text. 
            - Return only the code in your reply
            - Do not include any additional formatting, such as markdown code blocks
            - For formatting, use four space tabs, and do not allow any lines of code to 
              exceed 80 columns
            const books = [
              { title: 'Dune', category: 'fiction', id: 1 },
              { title: 'Frankenstein', category: 'fiction', id: 2 },
              { title: 'Moneyball', category: 'nonfiction', id: 3 },
            ];
            export default function BookList() {
              const listItems = books.map(book =>
                <li>
                  {book.title}
                </li>
              );
              return (
                <ul>{listItems}</ul>
              );
            }
            """, options: invokeOptions);
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            WriteAgentChatMessage(responseItem);
        }
    }
}
