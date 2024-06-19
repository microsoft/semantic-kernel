// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

namespace Optimization;

/// <summary>
/// This example shows how to use FrugalGPT techniques to reduce cost and improve performance of LLMs.
/// More information here: https://arxiv.org/abs/2305.05176.
/// </summary>
public sealed class FrugalGPT(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// One of the techniques is to reduce prompt size when using few-shot prompts.
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
                modelId: "text-embedding-ada-002",
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
        var memoryStore = new VolatileMemoryStore();
        var textEmbeddingGenerationService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Register optimization filter.
        kernel.PromptRenderFilters.Add(new FewShotPromptOptimizationFilter(memoryStore, textEmbeddingGenerationService));

        // Get result again and compare the usage.
        result = await kernel.InvokeAsync(function, arguments);

        Console.WriteLine(result); // Personal, Notifications
        Console.WriteLine(result.Metadata?["Usage"]?.AsJson()); // Total tokens: ~150
    }

    /// <summary>
    /// Few-shot prompt optimization filter which takes all examples from kernel arguments and selects first <see cref="TopN"/> examples,
    /// which are similar to original request.
    /// </summary>
    private sealed class FewShotPromptOptimizationFilter(
        IMemoryStore memoryStore,
        ITextEmbeddingGenerationService textEmbeddingGenerationService) : IPromptRenderFilter
    {
        /// <summary>
        /// Maximum number of examples to use which are similar to original request.
        /// </summary>
        private const int TopN = 5;

        /// <summary>
        /// Collection name to use in memory store.
        /// </summary>
        private const string CollectionName = "examples";

        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            // Get examples and original request from arguments.
            var examples = context.Arguments["Examples"] as List<string>;
            var request = context.Arguments["Request"] as string;

            if (examples is { Count: > 0 } && !string.IsNullOrEmpty(request))
            {
                var memoryRecords = new List<MemoryRecord>();

                // Generate embedding for each example.
                var embeddings = await textEmbeddingGenerationService.GenerateEmbeddingsAsync(examples);

                // Create memory record instances with example text and embedding.
                for (var i = 0; i < examples.Count; i++)
                {
                    memoryRecords.Add(MemoryRecord.LocalRecord(Guid.NewGuid().ToString(), examples[i], "description", embeddings[i]));
                }

                // Create collection and upsert all memory records for search.
                // It's possible to do it only once and re-use the same examples for future requests.
                await memoryStore.CreateCollectionAsync(CollectionName);
                await memoryStore.UpsertBatchAsync(CollectionName, memoryRecords).ToListAsync();

                // Generate embedding for original request.
                var requestEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(request);

                // Find top N examples which are similar to original request.
                var topNExamples = await memoryStore.GetNearestMatchesAsync(CollectionName, requestEmbedding, TopN).ToListAsync();

                // Override arguments to use only top N examples, which will be sent to LLM.
                context.Arguments["Examples"] = topNExamples.Select(l => l.Item1.Metadata.Text);
            }

            // Continue prompt rendering operation.
            await next(context);
        }
    }
}
