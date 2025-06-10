// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using ProcessFramework.Aspire.Shared;

var builder = WebApplication.CreateBuilder(args);

AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive", true);

builder.AddServiceDefaults();
builder.AddAzureOpenAIClient("openAiConnectionName");
builder.Services.AddKernel().AddAzureOpenAIChatCompletion("gpt-4o");

var app = builder.Build();

app.UseHttpsRedirection();

app.MapPost("/api/summary", async (Kernel kernel, SummarizeRequest summarizeRequest) =>
{
    ChatCompletionAgent summaryAgent =
    new()
    {
        Name = "SummarizationAgent",
        Instructions = "Summarize user input",
        Kernel = kernel
    };

    // Add a user message to the conversation
    var message = new ChatMessageContent(AuthorRole.User, summarizeRequest.TextToSummarize);

    // Generate the agent response(s)
    await foreach (ChatMessageContent response in summaryAgent.InvokeAsync(message).ConfigureAwait(false))
    {
        return response.Items.Last().ToString();
    }

    return null;
});

app.MapDefaultEndpoints();

app.Run();
