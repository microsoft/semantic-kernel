// Copyright (c) Microsoft. All rights reserved.

using Connectors.AI.PaLM.Skills;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using RepoUtils;

namespace TestPalmApi;

internal class Program
{
    const string PALM_API_KEY = "AIzaSyBckgGXO_DcMSmoRnE7UHGTKvfO7GuDU_8";//"[PUT YOUR PALM API KEY HERE]";
    const string Model = "text-bison-001";
    const string ModelEmbedding = "embedding-gecko-001";
    const string ModelToken = "chat-bison-001";
    static async Task Main(string[] args)
    {
        //run text embedding
        await RunEmbedAsync();

        //count token
        await RunTokenAsync();

        //run text completion
        await RunQaAsync();

        Console.ReadLine();
    }

    public static async Task RunTokenAsync()
    {
        var tokenskill = new TokenSkill(ModelToken, PALM_API_KEY);
        var count = await tokenskill.CountToken("hello world, I like this.");
        Console.WriteLine($"count token: {count}");
    }
    public static async Task RunEmbedAsync()
    {
        const string memoryCollectionName = "SKGitHub";

        var githubFiles = new Dictionary<string, string>()
        {
            ["https://github.com/microsoft/semantic-kernel/blob/main/README.md"]
                = "README: Installation, getting started, and how to contribute",
            ["https://github.com/microsoft/semantic-kernel/blob/main/samples/notebooks/dotnet/02-running-prompts-from-file.ipynb"]
                = "Jupyter notebook describing how to pass prompts from a file to a semantic skill or function",
            ["https://github.com/microsoft/semantic-kernel/blob/main/samples/notebooks/dotnet/00-getting-started.ipynb"]
                = "Jupyter notebook describing how to get started with the Semantic Kernel",
            ["https://github.com/microsoft/semantic-kernel/tree/main/samples/skills/ChatSkill/ChatGPT"]
                = "Sample demonstrating how to create a chat skill interfacing with ChatGPT",
            ["https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel/Memory/Volatile/VolatileMemoryStore.cs"]
                = "C# class that defines a volatile embedding store",
            ["https://github.com/microsoft/semantic-kernel/tree/main/samples/dotnet/KernelHttpServer/README.md"]
                = "README: How to set up a Semantic Kernel Service API using Azure Function Runtime v4",
            ["https://github.com/microsoft/semantic-kernel/tree/main/samples/apps/chat-summary-webapp-react/README.md"]
                = "README: README associated with a sample starter react-based chat summary webapp",
        };

        Console.WriteLine("======== PaLM Embedding ========");
        var builder = new KernelBuilder();
        builder
            .WithLogger(ConsoleLogger.Log)
            .WithPaLMTextEmbeddingGenerationService(ModelEmbedding, PALM_API_KEY)
            .WithPaLMTextCompletionService(Model, apiKey: PALM_API_KEY)
            .WithMemoryStorage(new VolatileMemoryStore());
        IKernel kernel = builder.Build();

        Console.WriteLine("Adding some GitHub file URLs and their descriptions to a volatile Semantic Memory.");
        var i = 0;
        foreach (var entry in githubFiles)
        {
            await kernel.Memory.SaveReferenceAsync(
                collection: memoryCollectionName,
                description: entry.Value,
                text: entry.Value,
                externalId: entry.Key,
                externalSourceName: "GitHub"
            );
            Console.WriteLine($"  URL {++i} saved");
        }

        string ask = "I love Jupyter notebooks, how should I get started?";
        Console.WriteLine("===========================\n" +
                            "Query: " + ask + "\n");

        var memories = kernel.Memory.SearchAsync(memoryCollectionName, ask, limit: 5, minRelevanceScore: 0.77);

        i = 0;
        await foreach (MemoryQueryResult memory in memories)
        {
            Console.WriteLine($"Result {++i}:");
            Console.WriteLine("  URL:     : " + memory.Metadata.Id);
            Console.WriteLine("  Title    : " + memory.Metadata.Description);
            Console.WriteLine("  Relevance: " + memory.Relevance);
            Console.WriteLine();
        }
    }
    public static async Task RunQaAsync()
    {
        Console.WriteLine("======== PaLM QA AI ========");
        Console.WriteLine("type 'exit' to close");
        List<Chat> chatList = new List<Chat>();
        IKernel kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            .WithPaLMTextCompletionService(Model, apiKey: PALM_API_KEY)
            .Build();

        const string FunctionDefinition = "{{$history}} Question: {{$input}}; Answer:";


        var questionAnswerFunction = kernel.CreateSemanticFunction(FunctionDefinition);
        while (true)
        {
            Console.Write("Q: ");
            var question = Console.ReadLine();
            if (string.IsNullOrEmpty(question)) continue;
            var context = new ContextVariables();
            context.Set("input", question);
            context.Set("history", GetHistory());
            try
            {
                var result = await kernel.RunAsync(context, questionAnswerFunction);
                Console.WriteLine($"A: {result.Result}");
                chatList.Add(new Chat() { Question = question, Answer = result.Result });
            }
            catch (Exception ex)
            {
                Console.WriteLine("try another question..");
            }

            /*
            foreach (var modelResult in result.ModelResults)
            {
                var resp = modelResult.GetPaLMResult();
                Console.WriteLine(resp.AsJson());
            }*/
            if (question == "exit")
            {

                break;
            }
        }


        string GetHistory()
        {
            var history = string.Empty;
            foreach (var chat in chatList)
            {
                history += $"Question: {chat.Question}; Answer:{chat.Answer};\n";
            }
            return history;
        }
    }
}

public class Chat
{
    public string Question { get; set; }
    public string Answer { get; set; }
}
