// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

var configuration = new ConfigurationBuilder()
    .AddUserSecrets<Program>()
    .AddEnvironmentVariables()
    .Build();

string? apiKey = configuration["OpenAI:ApiKey"];
string? modelId = configuration["OpenAI:ChatModelId"];

// Logger for program scope
ILogger logger = NullLogger.Instance;

ArgumentNullException.ThrowIfNull(apiKey);
ArgumentNullException.ThrowIfNull(modelId);

OpenAIAssistantAgent agent =
    await OpenAIAssistantAgent.CreateAsync(
        kernel: new(),
        OpenAIClientProvider.ForOpenAI(apiKey),
        new(modelId));

string threadId = await agent.CreateThreadAsync();

try
{
    ChatHistory messages = [];
    while (true)
    {
        Console.Write("\nUser: ");
        var input = Console.ReadLine();
        if (string.IsNullOrWhiteSpace(input)) { break; }

        await agent.AddChatMessageAsync(threadId, new(AuthorRole.User, input));

        Console.Write("\nAssistant: ");

        await foreach (StreamingChatMessageContent content in agent.InvokeStreamingAsync(threadId, messages))
        {
            Console.Write(content.Content);
        }

        Console.WriteLine();
    }
}
finally
{
    await agent.DeleteThreadAsync(threadId);
    await agent.DeleteAsync();
}
