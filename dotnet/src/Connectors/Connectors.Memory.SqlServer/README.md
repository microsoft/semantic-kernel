# Microsoft.SemanticKernel.Connectors.SqlServer

This connector uses the SQL Server database engine to implement Semantic Memory.

> [!IMPORTANT]  
> The features needed to use this connector are available in preview in Azure SQL only at the moment. Please take a look at the [Announcing EAP for Vector Support in Azure SQL Database](https://devblogs.microsoft.com/azure-sql/announcing-eap-native-vector-support-in-azure-sql-database/) for more information on how to enable the feature.

## Quick start

Create a new .NET console application:

```bash
dotnet new console --framework net8.0 -n MySemanticMemoryApp
```

Add the Semantic Kernel packages needed to create a Chatbot:

```bash
dotnet add package Microsoft.SemanticKernel
dotnet add package Microsoft.SemanticKernel.Connectors.OpenAI
```

Add `Microsoft.SemanticKernel.Connectors.SqlServer` to give your Chatbot memories:

```bash
dotnet add package Microsoft.SemanticKernel.Connectors.SqlServer --prerelease
```

Then you can use the following code to create a Chatbot with a memory that uses SQL Server:

```csharp
using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using Microsoft.SemanticKernel.Memory;

#pragma warning disable SKEXP0001, SKEXP0010

// Replace with your Azure OpenAI endpoint
const string AzureOpenAIEndpoint = "https://.openai.azure.com/";

// Replace with your Azure OpenAI API key
const string AzureOpenAIApiKey = "";

// Replace with your Azure OpenAI embedding deployment name
const string EmbeddingModelDeploymentName = "text-embedding-3-small";

// Replace with your Azure OpenAI chat completion deployment name
const string ChatModelDeploymentName = "gpt-4";

// Complete with your Azure SQL connection string
const string ConnectionString = "Data Source=.database.windows.net;Initial Catalog=;Authentication=Active Directory Default;Connection Timeout=30";

// Table where memories will be stored
const string TableName = "ChatMemories";


var kernel = Kernel.CreateBuilder()
    .AddAzureOpenAIChatCompletion(ChatModelDeploymentName, AzureOpenAIEndpoint, AzureOpenAIApiKey)
    .Build();

var memory = new MemoryBuilder()
    .WithSqlServerMemoryStore(ConnectionString, 1536)
    .WithAzureOpenAITextEmbeddingGeneration(EmbeddingModelDeploymentName, AzureOpenAIEndpoint, AzureOpenAIApiKey)
    .Build();

await memory.SaveInformationAsync(TableName, "With the new connector Microsoft.SemanticKernel.Connectors.SqlServer it is possible to efficiently store and retrieve memories thanks to the newly added vector support", "semantic-kernel-mssql");
await memory.SaveInformationAsync(TableName, "At the moment Microsoft.SemanticKernel.Connectors.SqlServer can be used only with Azure SQL", "semantic-kernel-azuresql");
await memory.SaveInformationAsync(TableName, "Azure SQL support for vectors is in Early Adopter Preview.", "azuresql-vector-eap");
await memory.SaveInformationAsync(TableName, "Pizza is one of the favourite food in the world.", "pizza-favourite-food");

var ai = kernel.GetRequiredService<IChatCompletionService>();
var chat = new ChatHistory("You are an AI assistant that helps people find information.");
var builder = new StringBuilder();
while (true)
{
    Console.Write("Question: ");
    var question = Console.ReadLine()!;

    Console.WriteLine("\nSearching information from the memory...");
    builder.Clear();
    await foreach (var result in memory.SearchAsync(TableName, question, limit: 3))
    {
        builder.AppendLine(result.Metadata.Text);
    }
    if (builder.Length != 0)
    {
        Console.WriteLine("\nFound information from the memory:");
        Console.WriteLine(builder.ToString());
    }

    Console.WriteLine("Answer: ");
    var contextToRemove = -1;
    if (builder.Length != 0)
    {
        builder.Insert(0, "Here's some additional information: ");
        contextToRemove = chat.Count;
        chat.AddUserMessage(builder.ToString());
    }

    chat.AddUserMessage(question);

    builder.Clear();
    await foreach (var message in ai.GetStreamingChatMessageContentsAsync(chat))
    {
        Console.Write(message);
        builder.Append(message.Content);
    }
    Console.WriteLine();
    chat.AddAssistantMessage(builder.ToString());

    if (contextToRemove >= 0)
        chat.RemoveAt(contextToRemove);

    Console.WriteLine();
}
```
