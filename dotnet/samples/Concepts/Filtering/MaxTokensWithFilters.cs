// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;

namespace Filtering;

/// <summary>
/// Property <see cref="OpenAIPromptExecutionSettings.MaxTokens"/> allows to specify maximum number of tokens to generate in one response.
/// In Semantic Kernel, auto function calling may perform multiple requests to AI model, but with the same max tokens value.
/// For example, in case when max tokens = 50, and 3 functions are expected to be called with 3 separate requests to AI model,
/// each request will have max tokens = 50, which in total will result in more tokens used.
/// This example shows how to limit token usage with <see cref="OpenAIPromptExecutionSettings.MaxTokens"/> property and filter
/// for all requests in the same auto function calling process.
/// </summary>
public sealed class MaxTokensWithFilters(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>Output max tokens value for demonstration purposes.</summary>
    private const int MaxTokens = 50;

    [Fact]
    public async Task ExampleAsync()
    {
        // Run example without filter. As a result, even though max tokens = 50, it takes 83 tokens to complete
        // the request with auto function calling process.
        await this.RunExampleAsync(includeFilter: false);

        // Output:
        // Invoking MoviePlugin-GetMovieTitles function.
        // Invoking MoviePlugin-GetDirectors function.
        // Invoking MoviePlugin-GetMovieDescriptions function.
        // Total output tokens used: 83

        // Run example with filter, which subtracts max tokens value based on previous requests.
        // As a result, it takes 50 tokens to complete the request, as specified in execution settings.
        await this.RunExampleAsync(includeFilter: true);

        // Output:
        // Invoking MoviePlugin-GetMovieTitles function.
        // Invoking MoviePlugin-GetDirectors function.
        // Invoking MoviePlugin-GetMovieDescriptions function.
        // Total output tokens used: 50
    }

    #region private

    private async Task RunExampleAsync(bool includeFilter)
    {
        // Define execution settings with max tokens and auto function calling enabled.
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            MaxTokens = MaxTokens,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Initialize kernel.
        var kernel = Kernel
            .CreateBuilder()
            .AddOpenAIChatCompletion("gpt-4", TestConfiguration.OpenAI.ApiKey)
            .Build();

        if (includeFilter)
        {
            // Add filter to control max tokens value.
            kernel.AutoFunctionInvocationFilters.Add(new MaxTokensFilter(executionSettings));
        }

        // Import plugin.
        kernel.ImportPluginFromObject(new MoviePlugin(this.Output));

        // Get chat completion service to work with chat history.
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Initialize chat history and define a goal/prompt for function calling process.
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Get an information about movie titles, directors and descriptions.");

        // Get a result for defined goal/prompt.
        var result = await chatCompletionService.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        // Get total output tokens used for all requests to AI model during the same auto function calling process.
        var totalOutputTokensUsed = GetChatHistoryOutputTokens([.. result, .. chatHistory]);

        // Output an information about used tokens.
        Console.WriteLine($"Total output tokens used: {totalOutputTokensUsed}");
    }

    /// <summary>Filter which controls max tokens value during function calling process.</summary>
    private sealed class MaxTokensFilter(OpenAIPromptExecutionSettings executionSettings) : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Get a last assistant message with information about used tokens.
            var assistantMessage = context.ChatHistory.LastOrDefault(l => l.Role == AuthorRole.Assistant);

            // Get tokens information from metadata.
            var messageTokens = GetOutputTokensFromMetadata(assistantMessage?.Metadata);

            // Subtract a value from execution settings to use less tokens during the next request.
            if (messageTokens.HasValue)
            {
                executionSettings.MaxTokens -= messageTokens.Value;
            }

            // Proceed with function calling process.
            await next(context);
        }
    }

    /// <summary>Movie plugin for demonstration purposes.</summary>
    private sealed class MoviePlugin(ITestOutputHelper output)
    {
        [KernelFunction]
        public List<string> GetMovieTitles()
        {
            output.WriteLine($"Invoking {nameof(MoviePlugin)}-{nameof(GetMovieTitles)} function.");

            return
            [
                "Forrest Gump",
                "The Sound of Music",
                "The Wizard of Oz",
                "Singin' in the Rain",
                "Harry Potter and the Sorcerer's Stone"
            ];
        }

        [KernelFunction]
        public List<string> GetDirectors()
        {
            output.WriteLine($"Invoking {nameof(MoviePlugin)}-{nameof(GetDirectors)} function.");

            return
            [
                "Robert Zemeckis",
                "Robert Wise",
                "Victor Fleming",
                "Stanley Donen and Gene Kelly",
                "Chris Columbus"
            ];
        }

        [KernelFunction]
        public List<string> GetMovieDescriptions()
        {
            output.WriteLine($"Invoking {nameof(MoviePlugin)}-{nameof(GetMovieDescriptions)} function.");

            return
            [
                "A heartfelt story of a man with a big heart who experiences key moments in 20th-century America.",
                "A young governess brings music and joy to a family in Austria.",
                "A young girl is swept away to a magical land and embarks on an adventurous journey home.",
                "A celebration of the golden age of Hollywood with iconic musical numbers.",
                "A young boy discovers he’s a wizard and begins his journey at Hogwarts School of Witchcraft and Wizardry."
            ];
        }
    }

    /// <summary>Helper method to get output tokens from entire chat history.</summary>
    private static int GetChatHistoryOutputTokens(ChatHistory? chatHistory)
    {
        var tokens = 0;

        if (chatHistory is null)
        {
            return tokens;
        }

        foreach (var message in chatHistory)
        {
            var messageTokens = GetOutputTokensFromMetadata(message.Metadata);

            if (messageTokens.HasValue)
            {
                tokens += messageTokens.Value;
            }
        }

        return tokens;
    }

    /// <summary>Helper method to get output tokens from message metadata.</summary>
    private static int? GetOutputTokensFromMetadata(IReadOnlyDictionary<string, object?>? metadata)
    {
        if (metadata is not null &&
            metadata.TryGetValue("Usage", out object? usageObject) &&
            usageObject is ChatTokenUsage usage)
        {
            return usage.OutputTokenCount;
        }

        return null;
    }

    #endregion
}
