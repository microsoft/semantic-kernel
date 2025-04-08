// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;

namespace ChatCompletion;

/// <summary>
/// Structured Outputs is a feature in OpenAI API that ensures the model will always generate responses based on provided JSON Schema.
/// This gives more control over model responses, allows to avoid model hallucinations and write simpler prompts without a need to be specific about response format.
/// More information here: <see href="https://platform.openai.com/docs/guides/structured-outputs/structured-outputs"/>.
/// </summary>
/// <remarks>
/// OpenAI Structured Outputs feature is available only in latest large language models, starting with GPT-4o.
/// More information here: <see href="https://platform.openai.com/docs/guides/structured-outputs/supported-models"/>.
/// </remarks>
/// <remarks>
/// Some keywords from JSON Schema are not supported in OpenAI Structured Outputs yet. For example, "format" keyword for strings is not supported.
/// It means that properties with types <see cref="DateTime"/>, <see cref="DateTimeOffset"/>, <see cref="DateOnly"/>, <see cref="TimeSpan"/>,
/// <see cref="TimeOnly"/>, <see cref="Uri"/> are not supported.
/// This information should be taken into consideration during response format type design.
/// More information here: <see href="https://platform.openai.com/docs/guides/structured-outputs/some-type-specific-keywords-are-not-yet-supported"/>.
/// </remarks>
public class OpenAI_StructuredOutputs(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This method shows how to enable Structured Outputs feature with <see cref="ChatResponseFormat"/> object by providing
    /// JSON schema of desired response format.
    /// </summary>
    [Fact]
    public async Task StructuredOutputsWithChatResponseFormatAsync()
    {
        // Initialize kernel.
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o-2024-08-06",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Initialize ChatResponseFormat object with JSON schema of desired response format.
        ChatResponseFormat chatResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
            jsonSchemaFormatName: "movie_result",
            jsonSchema: BinaryData.FromString("""
                {
                    "type": "object",
                    "properties": {
                        "Movies": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "Title": { "type": "string" },
                                    "Director": { "type": "string" },
                                    "ReleaseYear": { "type": "integer" },
                                    "Rating": { "type": "number" },
                                    "IsAvailableOnStreaming": { "type": "boolean" },
                                    "Tags": { "type": "array", "items": { "type": "string" } }
                                },
                                "required": ["Title", "Director", "ReleaseYear", "Rating", "IsAvailableOnStreaming", "Tags"],
                                "additionalProperties": false
                            }
                        }
                    },
                    "required": ["Movies"],
                    "additionalProperties": false
                }
                """),
            jsonSchemaIsStrict: true);

        // Specify response format by setting ChatResponseFormat object in prompt execution settings.
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ResponseFormat = chatResponseFormat
        };

        // Send a request and pass prompt execution settings with desired response format.
        var result = await kernel.InvokePromptAsync("What are the top 10 movies of all time?", new(executionSettings));

        // Deserialize string response to a strong type to access type properties.
        // At this point, the deserialization logic won't fail, because MovieResult type was described using JSON schema.
        // This ensures that response string is a serialized version of MovieResult type.
        var movieResult = JsonSerializer.Deserialize<MovieResult>(result.ToString())!;

        // Output the result.
        this.OutputResult(movieResult);

        // Output:

        // Title: The Lord of the Rings: The Fellowship of the Ring
        // Director: Peter Jackson
        // Release year: 2001
        // Rating: 8.8
        // Is available on streaming: True
        // Tags: Adventure,Drama,Fantasy

        // ...and more...
    }

    /// <summary>
    /// This method shows how to enable Structured Outputs feature with <see cref="Type"/> object by providing
    /// the type of desired response format. In this scenario, JSON schema will be created automatically based on provided type.
    /// </summary>
    [Fact]
    public async Task StructuredOutputsWithTypeInExecutionSettingsAsync()
    {
        // Initialize kernel.
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o-2024-08-06",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Specify response format by setting Type object in prompt execution settings.
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ResponseFormat = typeof(MovieResult)
        };

        // Send a request and pass prompt execution settings with desired response format.
        var result = await kernel.InvokePromptAsync("What are the top 10 movies of all time?", new(executionSettings));

        // Deserialize string response to a strong type to access type properties.
        // At this point, the deserialization logic won't fail, because MovieResult type was specified as desired response format.
        // This ensures that response string is a serialized version of MovieResult type.
        var movieResult = JsonSerializer.Deserialize<MovieResult>(result.ToString())!;

        // Output the result.
        this.OutputResult(movieResult);

        // Output:

        // Title: The Lord of the Rings: The Fellowship of the Ring
        // Director: Peter Jackson
        // Release year: 2001
        // Rating: 8.8
        // Is available on streaming: True
        // Tags: Adventure,Drama,Fantasy

        // ...and more...
    }

    /// <summary>
    /// This method shows how to use Structured Outputs feature in combination with Function Calling and OpenAI models.
    /// <see cref="EmailPlugin.GetEmails"/> function returns a <see cref="List{T}"/> of email bodies.
    /// As for final result, the desired response format should be <see cref="Email"/>, which contains additional <see cref="Email.Category"/> property.
    /// This shows how the data can be transformed with AI using strong types without additional instructions in the prompt.
    /// </summary>
    [Fact]
    public async Task StructuredOutputsWithFunctionCallingOpenAIAsync()
    {
        // Initialize kernel.
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o-2024-08-06",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        kernel.ImportPluginFromType<EmailPlugin>();

        // Specify response format by setting Type object in prompt execution settings and enable automatic function calling.
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ResponseFormat = typeof(EmailResult),
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Send a request and pass prompt execution settings with desired response format.
        var result = await kernel.InvokePromptAsync("Process the emails.", new(executionSettings));

        // Deserialize string response to a strong type to access type properties.
        // At this point, the deserialization logic won't fail, because EmailResult type was specified as desired response format.
        // This ensures that response string is a serialized version of EmailResult type.
        var emailResult = JsonSerializer.Deserialize<EmailResult>(result.ToString())!;

        // Output the result.
        this.OutputResult(emailResult);

        // Output:

        // Email #1
        // Body: Let's catch up over coffee this Saturday. It's been too long!
        // Category: Social

        // Email #2
        // Body: Please review the attached document and provide your feedback by EOD.
        // Category: Work

        // ...and more...
    }

    /// <summary>
    /// This method shows how to use Structured Outputs feature in combination with Function Calling and Azure OpenAI models.
    /// <see cref="EmailPlugin.GetEmails"/> function returns a <see cref="List{T}"/> of email bodies.
    /// As for final result, the desired response format should be <see cref="Email"/>, which contains additional <see cref="Email.Category"/> property.
    /// This shows how the data can be transformed with AI using strong types without additional instructions in the prompt.
    /// </summary>
    [Fact]
    public async Task StructuredOutputsWithFunctionCallingAzureOpenAIAsync()
    {
        // Initialize kernel.
        Kernel kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                credentials: new AzureCliCredential())
            .Build();

        kernel.ImportPluginFromType<EmailPlugin>();

        // Specify response format by setting Type object in prompt execution settings and enable automatic function calling.
        var executionSettings = new AzureOpenAIPromptExecutionSettings
        {
            ResponseFormat = typeof(EmailResult),
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Send a request and pass prompt execution settings with desired response format.
        var result = await kernel.InvokePromptAsync("Process the emails.", new(executionSettings));

        // Deserialize string response to a strong type to access type properties.
        // At this point, the deserialization logic won't fail, because EmailResult type was specified as desired response format.
        // This ensures that response string is a serialized version of EmailResult type.
        var emailResult = JsonSerializer.Deserialize<EmailResult>(result.ToString())!;

        // Output the result.
        this.OutputResult(emailResult);

        // Output:

        // Email #1
        // Body: Let's catch up over coffee this Saturday. It's been too long!
        // Category: Social

        // Email #2
        // Body: Please review the attached document and provide your feedback by EOD.
        // Category: Work

        // ...and more...
    }

    /// <summary>
    /// This method shows how to enable Structured Outputs feature with Azure OpenAI chat completion service.
    /// Model should be gpt-4o with version 2024-08-06 or later.
    /// Azure OpenAI chat completion API version should be 2024-08-01-preview or later.
    /// </summary>
    [Fact]
    public async Task StructuredOutputsWithAzureOpenAIAsync()
    {
        // Initialize kernel.
        Kernel kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                credentials: new AzureCliCredential())
            .Build();

        // Specify response format by setting Type object in prompt execution settings.
        var executionSettings = new AzureOpenAIPromptExecutionSettings
        {
            ResponseFormat = typeof(MovieResult)
        };

        // Send a request and pass prompt execution settings with desired response format.
        var result = await kernel.InvokePromptAsync("What are the top 10 movies of all time?", new(executionSettings));

        // Deserialize string response to a strong type to access type properties.
        // At this point, the deserialization logic won't fail, because MovieResult type was specified as desired response format.
        // This ensures that response string is a serialized version of MovieResult type.
        var movieResult = JsonSerializer.Deserialize<MovieResult>(result.ToString())!;

        // Output the result.
        this.OutputResult(movieResult);

        // Output:

        // Title: The Lord of the Rings: The Fellowship of the Ring
        // Director: Peter Jackson
        // Release year: 2001
        // Rating: 8.8
        // Is available on streaming: True
        // Tags: Adventure,Drama,Fantasy

        // ...and more...
    }

    /// <summary>
    /// This method shows how to enable Structured Outputs feature with Semantic Kernel functions from prompt
    /// using Semantic Kernel template engine.
    /// In this scenario, JSON Schema for response is specified in a prompt configuration file.
    /// </summary>
    [Fact]
    public async Task StructuredOutputsWithFunctionsFromPromptAsync()
    {
        // Initialize kernel.
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o-2024-08-06",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Initialize a path to plugin directory: Resources/Plugins/MoviePlugins/MoviePluginPrompt.
        var pluginDirectoryPath = Path.Combine(Directory.GetCurrentDirectory(), "Resources", "Plugins", "MoviePlugins", "MoviePluginPrompt");

        // Create a function from prompt.
        kernel.ImportPluginFromPromptDirectory(pluginDirectoryPath, pluginName: "MoviePlugin");

        var result = await kernel.InvokeAsync("MoviePlugin", "TopMovies");

        // Deserialize string response to a strong type to access type properties.
        // At this point, the deserialization logic won't fail, because MovieResult type was specified as desired response format.
        // This ensures that response string is a serialized version of MovieResult type.
        var movieResult = JsonSerializer.Deserialize<MovieResult>(result.ToString())!;

        // Output the result.
        this.OutputResult(movieResult);

        // Output:

        // Title: The Lord of the Rings: The Fellowship of the Ring
        // Director: Peter Jackson
        // Release year: 2001
        // Rating: 8.8
        // Is available on streaming: True
        // Tags: Adventure,Drama,Fantasy

        // ...and more...
    }

    /// <summary>
    /// This method shows how to enable Structured Outputs feature with Semantic Kernel functions from YAML
    /// using Semantic Kernel template engine.
    /// In this scenario, JSON Schema for response is specified in YAML prompt file.
    /// </summary>
    [Fact]
    public async Task StructuredOutputsWithFunctionsFromYamlAsync()
    {
        // Initialize kernel.
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o-2024-08-06",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Initialize a path to YAML function: Resources/Plugins/MoviePlugins/MoviePluginYaml.
        var functionPath = Path.Combine(Directory.GetCurrentDirectory(), "Resources", "Plugins", "MoviePlugins", "MoviePluginYaml", "TopMovies.yaml");

        // Load YAML prompt.
        var topMoviesYaml = File.ReadAllText(functionPath);

        // Import a function from YAML.
        var function = kernel.CreateFunctionFromPromptYaml(topMoviesYaml);
        kernel.ImportPluginFromFunctions("MoviePlugin", [function]);

        var result = await kernel.InvokeAsync("MoviePlugin", "TopMovies");

        // Deserialize string response to a strong type to access type properties.
        // At this point, the deserialization logic won't fail, because MovieResult type was specified as desired response format.
        // This ensures that response string is a serialized version of MovieResult type.
        var movieResult = JsonSerializer.Deserialize<MovieResult>(result.ToString())!;

        // Output the result.
        this.OutputResult(movieResult);

        // Output:

        // Title: The Lord of the Rings: The Fellowship of the Ring
        // Director: Peter Jackson
        // Release year: 2001
        // Rating: 8.8
        // Is available on streaming: True
        // Tags: Adventure,Drama,Fantasy

        // ...and more...
    }

    #region private

    /// <summary>Movie result struct that will be used as desired chat completion response format (structured output).</summary>
    private struct MovieResult
    {
        public List<Movie> Movies { get; set; }
    }

    /// <summary>Movie struct that will be used as desired chat completion response format (structured output).</summary>
    private struct Movie
    {
        public string Title { get; set; }

        public string Director { get; set; }

        public int ReleaseYear { get; set; }

        public double Rating { get; set; }

        public bool IsAvailableOnStreaming { get; set; }

        public List<string> Tags { get; set; }
    }

    private sealed class EmailResult
    {
        public List<Email> Emails { get; set; }
    }

    private sealed class Email
    {
        public string Body { get; set; }

        public string Category { get; set; }
    }

    /// <summary>Plugin to simulate RAG scenario and return collection of data.</summary>
    private sealed class EmailPlugin
    {
        /// <summary>Function to simulate RAG scenario and return collection of data.</summary>
        [KernelFunction]
        private List<string> GetEmails()
        {
            return
            [
                "Hey, just checking in to see how you're doing!",
                "Can you pick up some groceries on your way back home? We need milk and bread.",
                "Happy Birthday! Wishing you a fantastic day filled with love and joy.",
                "Let's catch up over coffee this Saturday. It's been too long!",
                "Please review the attached document and provide your feedback by EOD.",
            ];
        }
    }

    /// <summary>Helper method to output <see cref="MovieResult"/> object content.</summary>
    private void OutputResult(MovieResult movieResult)
    {
        for (var i = 0; i < movieResult.Movies.Count; i++)
        {
            var movie = movieResult.Movies[i];

            this.Output.WriteLine($"Movie #{i + 1}");
            this.Output.WriteLine($"Title: {movie.Title}");
            this.Output.WriteLine($"Director: {movie.Director}");
            this.Output.WriteLine($"Release year: {movie.ReleaseYear}");
            this.Output.WriteLine($"Rating: {movie.Rating}");
            this.Output.WriteLine($"Is available on streaming: {movie.IsAvailableOnStreaming}");
            this.Output.WriteLine($"Tags: {string.Join(",", movie.Tags)}");
        }
    }

    /// <summary>Helper method to output <see cref="EmailResult"/> object content.</summary>
    private void OutputResult(EmailResult emailResult)
    {
        for (var i = 0; i < emailResult.Emails.Count; i++)
        {
            var email = emailResult.Emails[i];

            this.Output.WriteLine($"Email #{i + 1}");
            this.Output.WriteLine($"Body: {email.Body}");
            this.Output.WriteLine($"Category: {email.Category}");
        }
    }

    #endregion
}
