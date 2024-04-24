// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Prompty.Extension;
using Xunit;

namespace SemanticKernel.Functions.Prompty.UnitTests;
public sealed class PromptyTest
{
    [Fact]
    public async Task ChatPromptyTemplateTestAsync()
    {
        var modelId = "gpt-35-turbo-16k";
        var endPoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new Exception("AZURE_OPENAI_ENDPOINT is not set");
        var key = Environment.GetEnvironmentVariable("AZURE_OPENAI_API_KEY") ?? throw new Exception("AZURE_OPENAI_KEY is not set");
        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(modelId, endPoint, key)
            .Build();

        var cwd = Directory.GetCurrentDirectory();
        var chatPromptyPath = Path.Combine(cwd, "TestData", "chat.prompty");
        var function = kernel.CreateFunctionFromPrompty(chatPromptyPath);
        // create a dynamic customer object
        // customer contains the following properties
        // - firstName
        // - lastName
        // - age
        // - membership
        // - orders []
        //  - name
        //  - description
        var customer = new
        {
            firstName = "John",
            lastName = "Doe",
            age = 30,
            membership = "Gold",
            orders = new[]
            {
                new { name = "apple", description = "2 fuji apples", date = "2024/04/01" },
                new { name = "banana", description = "1 free banana from amazon banana hub", date = "2024/04/03" },
            },
        };

        // create a list of documents
        // documents contains the following properties
        // - id
        // - title
        // - content
        var documents = new[]
        {
            new { id = "1", title = "apple", content = "2 apples"},
            new { id = "2", title = "banana", content = "3 bananas"},
        };

        // create chat history
        // each chat message contains the following properties
        // - role (system, user, assistant)
        // - content

        var chatHistory = new[]
        {
            new { role = "user", content = "When is the last time I bought apple? Give me specific date and year" },
        };

        // create
        var result = await kernel.InvokeAsync(function, arguments: new()
        {
            { "customer", customer },
            { "documentation", documents },
            { "history", chatHistory },
        });

        Assert.IsType<OpenAIChatMessageContent>(result.GetValue<OpenAIChatMessageContent>());

        if (result.GetValue< OpenAIChatMessageContent>() is OpenAIChatMessageContent openAIChatMessageContent)
        {
            Assert.Equal(AuthorRole.Assistant, openAIChatMessageContent.Role);
            Assert.Contains("2024", openAIChatMessageContent.Content, StringComparison.InvariantCultureIgnoreCase);
        }
    }
}
