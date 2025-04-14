// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

var builder = WebApplication.CreateBuilder(args);

AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive", true);

builder.AddServiceDefaults();
builder.AddAzureOpenAIClient("openAiConnectionName");
builder.Services.AddKernel().AddAzureOpenAIChatCompletion("gpt-4o");
builder.Services.AddSingleton<ChatCompletionAgent>(builder =>
{
    return new()
    {
        Name = "SummarizationAgent",
        Instructions = "Summarize user input",
        Kernel = builder.GetRequiredService<Kernel>()
    };
});

var app = builder.Build();

app.UseHttpsRedirection();

app.MapGet("/agent/details", (ChatCompletionAgent agent) =>
{
    var details = new
    {
        Name = agent.Name,
        Instructions = agent.Instructions
    };
    return JsonSerializer.Serialize(details);
});


app.MapPost("/agent/invoke", async (ChatCompletionAgent agent, HttpResponse response, ChatHistory history) =>
{
    response.Headers.Append("Content-Type", "application/json");

    var thread = new ChatHistoryAgentThread();

    await foreach (var chatResponse in agent.InvokeAsync(history, thread).ConfigureAwait(false))
    {
        chatResponse.Message.AuthorName = agent.Name;

        return JsonSerializer.Serialize(chatResponse.Message);
    }

    return null;
});

app.MapPost("/agent/invoke-streaming", async (ChatCompletionAgent agent, HttpResponse response, ChatHistory history) =>
{
    response.Headers.Append("Content-Type", "application/jsonl");

    var thread = new ChatHistoryAgentThread();

    var chatResponse = agent.InvokeStreamingAsync(history, thread).ConfigureAwait(false);
    await foreach (var delta in chatResponse)
    {
        var message = new StreamingChatMessageContent(AuthorRole.Assistant, delta.Message.Content)
        {
            AuthorName = agent.Name
        };

        await response.WriteAsync(JsonSerializer.Serialize(message)).ConfigureAwait(false);
        await response.Body.FlushAsync().ConfigureAwait(false);
    }
})
.WithName("InvokeSummaryAgentStreaming");

app.MapDefaultEndpoints();

app.Run();
