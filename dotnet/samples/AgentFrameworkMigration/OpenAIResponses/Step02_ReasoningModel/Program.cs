// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;

#pragma warning disable OPENAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY") ?? throw new InvalidOperationException("OPENAI_API_KEY is not set.");
var model = System.Environment.GetEnvironmentVariable("OPENAI_MODEL") ?? "o4-mini";
var userInput =
    """
    Instructions:
    - Given the React component below, think about it and change it so that nonfiction books have red
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
    """;

Console.WriteLine($"User Input: {userInput}");

await SKAgentAsync();
await SKAgent_As_AFAgentAsync();
await AFAgentAsync();

async Task SKAgentAsync()
{
    Console.WriteLine("\n=== SK Agent ===\n");

    var responseClient = new OpenAIClient(apiKey).GetResponsesClient(model);
    OpenAIResponseAgent agent = new(responseClient)
    {
        Name = "Thinker",
        Instructions = "You are good at thinking hard before answering.",
        StoreEnabled = true
    };

    var agentOptions = new OpenAIResponseAgentInvokeOptions()
    {
        ResponseCreationOptions = new()
        {
            MaxOutputTokenCount = 8000,
            ReasoningOptions = new()
            {
                ReasoningEffortLevel = OpenAI.Responses.ResponseReasoningEffortLevel.High,
                ReasoningSummaryVerbosity = OpenAI.Responses.ResponseReasoningSummaryVerbosity.Detailed
            }
        }
    };

    Microsoft.SemanticKernel.Agents.AgentThread? thread = null;
    await foreach (var item in agent.InvokeAsync(userInput, thread, agentOptions))
    {
        thread = item.Thread;
        foreach (var content in item.Message.Items)
        {
            if (content is ReasoningContent thinking)
            {
                Console.Write($"Thinking: \n{thinking}\n---\n");
            }
            else if (content is Microsoft.SemanticKernel.TextContent text)
            {
                Console.Write($"Assistant: {text}");
            }
        }
        Console.WriteLine(item.Message);
    }

    Console.WriteLine("---");
    var userMessage = new ChatMessageContent(AuthorRole.User, userInput);
    thread = null;
    await foreach (var item in agent.InvokeStreamingAsync(userMessage, thread, agentOptions))
    {
        thread = item.Thread;
        foreach (var content in item.Message.Items)
        {
            // Currently SK Agent doesn't output thinking in streaming mode.
            // SK Issue: https://github.com/microsoft/semantic-kernel/issues/13046
            // OpenAI SDK Issue: https://github.com/openai/openai-dotnet/issues/643
            if (content is StreamingReasoningContent thinking)
            {
                Console.WriteLine($"Thinking: [{thinking}]");
                continue;
            }

            if (content is StreamingTextContent text)
            {
                Console.WriteLine($"Response: [{text}]");
            }
        }
    }
}

async Task SKAgent_As_AFAgentAsync()
{
    Console.WriteLine("\n=== SK Agent Converted as an AF Agent ===\n");

    var responseClient = new OpenAIClient(apiKey).GetResponsesClient(model);

#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

    OpenAIResponseAgent skAgent = new(responseClient)
    {
        Name = "Thinker",
        Instructions = "You are at thinking hard before answering.",
        StoreEnabled = true
    };

    var agent = skAgent.AsAIAgent();

#pragma warning restore SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

    var thread = agent.GetNewThread();
    var agentOptions = new ChatClientAgentRunOptions(new()
    {
        MaxOutputTokens = 8000,
        Reasoning = new()
        {
            Effort = ReasoningEffort.High,
            Output = ReasoningOutput.Full
        }
    });

    var result = await agent.RunAsync(userInput, thread, agentOptions);

    // Retrieve the thinking as a full text block requires flattening multiple TextReasoningContents from multiple messages content lists.
    string assistantThinking = string.Join("\n", result.Messages
        .SelectMany(m => m.Contents)
        .OfType<TextReasoningContent>()
        .Select(trc => trc.Text));

    var assistantText = result.Text;
    Console.WriteLine($"Thinking: \n{assistantThinking}\n---\n");
    Console.WriteLine($"Assistant: \n{assistantText}\n---\n");

    Console.WriteLine("---");
    await foreach (var update in agent.RunStreamingAsync(userInput, thread, agentOptions))
    {
        var thinkingContents = update.Contents
            .OfType<TextReasoningContent>()
            .Select(trc => trc.Text)
            .ToList();

        if (thinkingContents.Count != 0)
        {
            Console.WriteLine($"Thinking: [{string.Join("\n", thinkingContents)}]");
            continue;
        }

        Console.WriteLine($"Response: [{update.Text}]");
    }
}

async Task AFAgentAsync()
{
    Console.WriteLine("\n=== AF Agent ===\n");

    var agent = new OpenAIClient(apiKey).GetResponsesClient(model)
        .CreateAIAgent(name: "Thinker", instructions: "You are at thinking hard before answering.");

    var thread = agent.GetNewThread();
    var agentOptions = new ChatClientAgentRunOptions(new()
    {
        MaxOutputTokens = 8000,
        Reasoning = new()
        {
            Effort = ReasoningEffort.High,
            Output = ReasoningOutput.Full
        }
    });

    var result = await agent.RunAsync(userInput, thread, agentOptions);

    // Retrieve the thinking as a full text block requires flattening multiple TextReasoningContents from multiple messages content lists.
    string assistantThinking = string.Join("\n", result.Messages
        .SelectMany(m => m.Contents)
        .OfType<TextReasoningContent>()
        .Select(trc => trc.Text));

    var assistantText = result.Text;
    Console.WriteLine($"Thinking: \n{assistantThinking}\n---\n");
    Console.WriteLine($"Assistant: \n{assistantText}\n---\n");

    Console.WriteLine("---");
    await foreach (var update in agent.RunStreamingAsync(userInput, thread, agentOptions))
    {
        var thinkingContents = update.Contents
            .OfType<TextReasoningContent>()
            .Select(trc => trc.Text)
            .ToList();

        if (thinkingContents.Count != 0)
        {
            Console.WriteLine($"Thinking: [{string.Join("\n", thinkingContents)}]");
            continue;
        }

        Console.WriteLine($"Response: [{update.Text}]");
    }
}
