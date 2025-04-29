// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.Services;

namespace Optimization;

/// <summary>
/// This example shows how to use FrugalGPT techniques to reduce cost and improve LLM-related task performance.
/// More information here: https://arxiv.org/abs/2305.05176.
/// </summary>
public sealed class FrugalGPTWithFilters(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// One of the FrugalGPT techniques is to reduce prompt size when using few-shot prompts.
    /// If prompt contains a lof of examples to help LLM to provide the best result, it's possible to send only a couple of them to reduce amount of tokens.
    /// Vector similarity can be used to pick the best examples from example set for specific request.
    /// Following example shows how to optimize email classification request by reducing prompt size with vector similarity search.
    /// </summary>
    [Fact]
    public async Task ReducePromptSizeAsync()
    {
        // Define email classification examples with email body and labels.
        var examples = new List<string>
        {
            "Hey, just checking in to see how you're doing! - Personal",
            "Can you pick up some groceries on your way back home? We need milk and bread. - Personal, Tasks",
            "Happy Birthday! Wishing you a fantastic day filled with love and joy. - Personal",
            "Let's catch up over coffee this Saturday. It's been too long! - Personal, Events",
            "Please review the attached document and provide your feedback by EOD. - Work",
            "Our team meeting is scheduled for 10 AM tomorrow in the main conference room. - Work",
            "The quarterly financial report is due next Monday. Ensure all data is updated. - Work, Tasks",
            "Can you send me the latest version of the project plan? Thanks! - Work",
            "You're invited to our annual summer picnic! RSVP by June 25th. - Events",
            "Join us for a webinar on digital marketing trends this Thursday at 3 PM. - Events",
            "Save the date for our charity gala on September 15th. We hope to see you there! - Events",
            "Don't miss our customer appreciation event next week. Sign up now! - Events, Notifications",
            "Your order has been shipped and will arrive by June 20th. - Notifications",
            "We've updated our policies. Please review the changes. - Notifications",
            "Your username was successfully changed. If this wasn't you, contact support immediately. - Notifications",
            "The system upgrade will occur this weekend. - Notifications, Work",
            "Don't forget to submit your timesheet by 5 PM today. - Tasks, Work",
            "Pick up the dry cleaning before they close at 7 PM. - Tasks",
            "Complete the online training module by the end of the week. - Tasks, Work",
            "Send out the meeting invites for next week's project kickoff. - Tasks, Work"
        };

        // Initialize kernel with chat completion and embedding generation services.
        // It's possible to combine different models from different AI providers to achieve the lowest token usage.
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .AddOpenAITextEmbeddingGeneration(
                modelId: "text-embedding-3-small",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Initialize few-shot prompt.
        var function = kernel.CreateFunctionFromPrompt(
            new()
            {
                Template =
                """
                Available classification labels: Personal, Work, Events, Notifications, Tasks
                Email classification examples:
                {{#each Examples}}
                    {{this}}
                {{/each}}

                Email body to classify:
                {{Request}}
                """,
                TemplateFormat = "handlebars"
            },
            new HandlebarsPromptTemplateFactory()
        );

        // Define arguments with few-shot examples and actual email for classification.
        var arguments = new KernelArguments
        {
            ["Examples"] = examples,
            ["Request"] = "Your dentist appointment is tomorrow at 10 AM. Please remember to bring your insurance card."
        };

        // Invoke defined function to see initial result.
        var result = await kernel.InvokeAsync(function, arguments);

        Console.WriteLine(result); // Personal, Notifications
        Console.WriteLine(result.Metadata?["Usage"]?.AsJson()); // Total tokens: ~430

        // Add few-shot prompt optimization filter.
        // The filter uses in-memory store for vector similarity search and text embedding generation service to generate embeddings.
        var vectorStore = new InMemoryVectorStore();
        var textEmbeddingGenerationService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Register optimization filter.
        kernel.PromptRenderFilters.Add(new FewShotPromptOptimizationFilter(vectorStore, textEmbeddingGenerationService));

        // Get result again and compare the usage.
        result = await kernel.InvokeAsync(function, arguments);

        Console.WriteLine(result); // Personal, Notifications
        Console.WriteLine(result.Metadata?["Usage"]?.AsJson()); // Total tokens: ~150
    }

    /// <summary>
    /// LLM cascade technique allows to use multiple LLMs sequentially starting from cheaper model,
    /// evaluate LLM result and return it in case it meets the quality criteria. Otherwise, proceed with next LLM in queue,
    /// until the result will be acceptable.
    /// Following example uses mock result generation and evaluation for demonstration purposes.
    /// Result evaluation examples including BERTScore, BLEU, METEOR and COMET metrics can be found here:
    /// https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/Demos/QualityCheck.
    /// </summary>
    [Fact]
    public async Task LLMCascadeAsync()
    {
        // Create kernel builder.
        var builder = Kernel.CreateBuilder();

        // Register chat completion services for demonstration purposes.
        // This registration is similar to AddAzureOpenAIChatCompletion and AddOpenAIChatCompletion methods.
        builder.Services.AddSingleton<IChatCompletionService>(new MockChatCompletionService("model1", "Hi there! I'm doing well, thank you! How about yourself?"));
        builder.Services.AddSingleton<IChatCompletionService>(new MockChatCompletionService("model2", "Hello! I'm great, thanks for asking. How are you doing today?"));
        builder.Services.AddSingleton<IChatCompletionService>(new MockChatCompletionService("model3", "Hey! I'm fine, thanks. How's your day going so far?"));

        // Register LLM cascade filter with model execution order, acceptance criteria for result and service for output.
        // In real use-cases, execution order should start from cheaper to more expensive models.
        // If first model will produce acceptable result, then it will be returned immediately.
        builder.Services.AddSingleton<IFunctionInvocationFilter>(new LLMCascadeFilter(
            modelExecutionOrder: ["model1", "model2", "model3"],
            acceptanceCriteria: result => result.Contains("Hey!"),
            output: this.Output));

        // Build kernel.
        var kernel = builder.Build();

        // Send a request.
        var result = await kernel.InvokePromptAsync("Hi, how are you today?");

        Console.WriteLine($"\nFinal result: {result}");

        // Output:
        // Executing request with model: model1
        // Result from model1: Hi there! I'm doing well, thank you! How about yourself?
        // Result does not meet the acceptance criteria, moving to the next model.

        // Executing request with model: model2
        // Result from model2: Hello! I'm great, thanks for asking. How are you doing today?
        // Result does not meet the acceptance criteria, moving to the next model.

        // Executing request with model: model3
        // Result from model3: Hey! I'm fine, thanks. How's your day going so far?
        // Returning result as it meets the acceptance criteria.

        // Final result: Hey! I'm fine, thanks. How's your day going so far?
    }

    /// <summary>
    /// Few-shot prompt optimization filter which takes all examples from kernel arguments and selects first <see cref="TopN"/> examples,
    /// which are similar to original request.
    /// </summary>
    private sealed class FewShotPromptOptimizationFilter(
        IVectorStore vectorStore,
        ITextEmbeddingGenerationService textEmbeddingGenerationService) : IPromptRenderFilter
    {
        /// <summary>
        /// Maximum number of examples to use which are similar to original request.
        /// </summary>
        private const int TopN = 5;

        /// <summary>
        /// Collection name to use in vector store.
        /// </summary>
        private const string CollectionName = "examples";

        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            // Get examples and original request from arguments.
            var examples = context.Arguments["Examples"] as List<string>;
            var request = context.Arguments["Request"] as string;

            if (examples is { Count: > 0 } && !string.IsNullOrEmpty(request))
            {
                var exampleRecords = new List<ExampleRecord>();

                // Generate embedding for each example.
                var embeddings = await textEmbeddingGenerationService.GenerateEmbeddingsAsync(examples);

                // Create vector store record instances with example text and embedding.
                for (var i = 0; i < examples.Count; i++)
                {
                    exampleRecords.Add(new ExampleRecord
                    {
                        Id = Guid.NewGuid().ToString(),
                        Example = examples[i],
                        ExampleEmbedding = embeddings[i]
                    });
                }

                // Create collection and upsert all vector store records for search.
                // It's possible to do it only once and re-use the same examples for future requests.
                var collection = vectorStore.GetCollection<string, ExampleRecord>(CollectionName);
                await collection.CreateCollectionIfNotExistsAsync(context.CancellationToken);

                await collection.UpsertAsync(exampleRecords, cancellationToken: context.CancellationToken);

                // Generate embedding for original request.
                var requestEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(request, cancellationToken: context.CancellationToken);

                // Find top N examples which are similar to original request.
                var topNExamples = (await collection.SearchEmbeddingAsync(requestEmbedding, top: TopN, cancellationToken: context.CancellationToken)
                    .ToListAsync(context.CancellationToken)).Select(l => l.Record).ToList();

                // Override arguments to use only top N examples, which will be sent to LLM.
                context.Arguments["Examples"] = topNExamples.Select(l => l.Example);
            }

            // Continue prompt rendering operation.
            await next(context);
        }
    }

    /// <summary>
    /// Example of LLM cascade filter which will invoke a function using multiple LLMs in specific order,
    /// until the result will meet specified acceptance criteria.
    /// </summary>
    private sealed class LLMCascadeFilter(
        List<string> modelExecutionOrder,
        Predicate<string> acceptanceCriteria,
        ITestOutputHelper output) : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            // Get registered chat completion services from kernel.
            var registeredServices = context.Kernel
                .GetAllServices<IChatCompletionService>()
                .Select(service => (ModelId: service.GetModelId()!, Service: service));

            // Define order of execution.
            var order = modelExecutionOrder
                .Select((value, index) => new { Value = value, Index = index })
                .ToDictionary(k => k.Value, v => v.Index);

            // Sort services by specified order.
            var orderedServices = registeredServices.OrderBy(service => order[service.ModelId]);

            // Try to invoke a function with each service and check the result.
            foreach (var service in orderedServices)
            {
                // Define execution settings with model ID.
                context.Arguments.ExecutionSettings = new Dictionary<string, PromptExecutionSettings>
                {
                    { PromptExecutionSettings.DefaultServiceId, new() { ModelId = service.ModelId } }
                };

                output.WriteLine($"Executing request with model: {service.ModelId}");

                // Invoke a function.
                await next(context);

                // Get a result.
                var result = context.Result.ToString()!;

                output.WriteLine($"Result from {service.ModelId}: {result}");

                // Check if result meets specified acceptance criteria.
                // If yes, stop execution loop, so last result will be returned.
                if (acceptanceCriteria(result))
                {
                    output.WriteLine("Returning result as it meets the acceptance criteria.");
                    return;
                }

                // Otherwise, proceed with next model.
                output.WriteLine("Result does not meet the acceptance criteria, moving to the next model.\n");
            }

            // If LLMs didn't return acceptable result, the last result will be returned.
            // It's also possible to throw an exception in such cases if needed.
            // throw new Exception("Models didn't return a result that meets the acceptance criteria").
        }
    }

    /// <summary>
    /// Mock chat completion service for demonstration purposes.
    /// </summary>
    private sealed class MockChatCompletionService(string modelId, string mockResult) : IChatCompletionService
    {
        public IReadOnlyDictionary<string, object?> Attributes => new Dictionary<string, object?> { { AIServiceExtensions.ModelIdKey, modelId } };

        public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
            ChatHistory chatHistory,
            PromptExecutionSettings? executionSettings = null,
            Kernel? kernel = null,
            CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<ChatMessageContent>>([new ChatMessageContent(AuthorRole.Assistant, mockResult)]);
        }

        public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
            ChatHistory chatHistory,
            PromptExecutionSettings? executionSettings = null,
            Kernel? kernel = null,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            yield return new StreamingChatMessageContent(AuthorRole.Assistant, mockResult);
        }
    }

    private sealed class ExampleRecord
    {
        [VectorStoreRecordKey]
        public string Id { get; set; }

        [VectorStoreRecordData]
        public string Example { get; set; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> ExampleEmbedding { get; set; }
    }
}
