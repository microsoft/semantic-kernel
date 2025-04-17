// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using Google.Apis.Auth.OAuth2;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Google;
using OpenAI.Chat;
using Directory = System.IO.Directory;
using File = System.IO.File;

namespace ChatCompletion;

/// <summary>
/// Structured Outputs is a feature in Vertex API that ensures the model will always generate responses based on provided JSON Schema.
/// This gives more control over model responses, allows to avoid model hallucinations and write simpler prompts without a need to be specific about response format.
/// More information here: <see href="https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output#model_behavior_and_response_schema"/>.
/// </summary>
public class Google_GeminiStructuredOutputs(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This method shows how to enable Structured Outputs feature with <see cref="ChatResponseFormat"/> object by providing
    /// JSON schema of desired response format.
    /// </summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task StructuredOutputsWithTypeInExecutionSettings(bool useGoogleAI)
    {
        var kernel = this.InitializeKernel(useGoogleAI);

        GeminiPromptExecutionSettings executionSettings = new()
        {
            ResponseMimeType = "application/json",
            // Send a request and pass prompt execution settings with desired response schema.
            ResponseSchema = typeof(User)
        };

        var result = await kernel.InvokePromptAsync("Extract the data from the following text: My name is Praveen", new(executionSettings));

        var user = JsonSerializer.Deserialize<User>(result.ToString())!;
        this.OutputResult(user);

        // Send a request and pass prompt execution settings with desired response schema.
        executionSettings.ResponseSchema = typeof(MovieResult);
        result = await kernel.InvokePromptAsync("What are the top 10 movies of all time?", new(executionSettings));

        // Deserialize string response to a strong type to access type properties.
        // At this point, the deserialization logic won't fail, because MovieResult type was described using JSON schema.
        // This ensures that response string is a serialized version of MovieResult type.
        var movieResult = JsonSerializer.Deserialize<MovieResult>(result.ToString())!;

        // Output the result.
        this.OutputResult(movieResult);
    }

    /// <summary>
    /// This method shows how to use Structured Outputs feature in combination with Function Calling and Gemini models.
    /// <see cref="EmailPlugin.GetEmails"/> function returns a <see cref="List{T}"/> of email bodies.
    /// As for final result, the desired response format should be <see cref="Email"/>, which contains additional <see cref="Email.Category"/> property.
    /// This shows how the data can be transformed with AI using strong types without additional instructions in the prompt.
    /// </summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task StructuredOutputsWithFunctionCalling(bool useGoogleAI)
    {
        // Initialize kernel.
        var kernel = this.InitializeKernel(useGoogleAI);

        kernel.ImportPluginFromType<EmailPlugin>();

        // Specify response format by setting Type object in prompt execution settings and enable automatic function calling.
        var executionSettings = new GeminiPromptExecutionSettings
        {
            ResponseSchema = typeof(EmailResult),
            ResponseMimeType = "application/json",
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
    }

    /// <summary>
    /// This method shows how to enable Structured Outputs feature with Semantic Kernel functions from prompt
    /// using Semantic Kernel template engine.
    /// In this scenario, JSON Schema for response is specified in a prompt configuration file.
    /// </summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task StructuredOutputsWithFunctionsFromPrompt(bool useGoogleAI)
    {
        // Initialize kernel.
        var kernel = this.InitializeKernel(useGoogleAI);

        // Initialize a path to plugin directory: Resources/Plugins/MoviePlugins/MoviePluginPrompt.
        var pluginDirectoryPath = Path.Combine(Directory.GetCurrentDirectory(), "Resources", "Plugins", "MoviePlugins", "MoviePluginPrompt");

        // Create a function from prompt.
        kernel.ImportPluginFromPromptDirectory(pluginDirectoryPath, pluginName: "MoviePlugin");

        var executionSettings = new GeminiPromptExecutionSettings
        {
            ResponseSchema = typeof(MovieResult),
            ResponseMimeType = "application/json",
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        var result = await kernel.InvokeAsync("MoviePlugin", "TopMovies", new(executionSettings));

        // Deserialize string response to a strong type to access type properties.
        // At this point, the deserialization logic won't fail, because MovieResult type was specified as desired response format.
        // This ensures that response string is a serialized version of MovieResult type.
        var movieResult = JsonSerializer.Deserialize<MovieResult>(result.ToString())!;

        // Output the result.
        this.OutputResult(movieResult);
    }

    /// <summary>
    /// This method shows how to enable Structured Outputs feature with Semantic Kernel functions from YAML
    /// using Semantic Kernel template engine.
    /// In this scenario, JSON Schema for response is specified in YAML prompt file.
    /// </summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task StructuredOutputsWithFunctionsFromYaml(bool useGoogleAI)
    {
        // Initialize kernel.
        var kernel = this.InitializeKernel(useGoogleAI);

        // Initialize a path to YAML function: Resources/Plugins/MoviePlugins/MoviePluginYaml.
        var functionPath = Path.Combine(Directory.GetCurrentDirectory(), "Resources", "Plugins", "MoviePlugins", "MoviePluginYaml", "TopMovies.yaml");

        // Load YAML prompt.
        var topMoviesYaml = File.ReadAllText(functionPath);

        // Import a function from YAML.
        var function = kernel.CreateFunctionFromPromptYaml(topMoviesYaml);
        kernel.ImportPluginFromFunctions("MoviePlugin", [function]);

        var executionSettings = new GeminiPromptExecutionSettings
        {
            ResponseSchema = typeof(MovieResult),
            ResponseMimeType = "application/json",
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        var result = await kernel.InvokeAsync("MoviePlugin", "TopMovies", new(executionSettings));

        // Deserialize string response to a strong type to access type properties.
        // At this point, the deserialization logic won't fail, because MovieResult type was specified as desired response format.
        // This ensures that response string is a serialized version of MovieResult type.
        var movieResult = JsonSerializer.Deserialize<MovieResult>(result.ToString())!;

        // Output the result.
        this.OutputResult(movieResult);
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

        public MovieGenre? Genre { get; set; }

        public List<string> Tags { get; set; }
    }

    private enum MovieGenre
    {
        Action,
        Adventure,
        Comedy,
        Drama,
        Fantasy,
        Horror,
        Mystery,
        Romance,
        SciFi,
        Thriller,
        Western
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

    [Description("User")]
    private sealed class User
    {
        [Description("This field contains name of user")]
        [JsonPropertyName("name")]
        [AllowNull]
        public string? Name { get; set; }

        [Description("This field contains user email")]
        [JsonPropertyName("email")]
        [AllowNull]
        public string? Email { get; set; }

        [Description("This field contains user age")]
        [JsonPropertyName("age")]
        [AllowNull]
        public int? Age { get; set; }
    }

    /// <summary>Helper method to output <see cref="MovieResult"/> object content.</summary>
    private void OutputResult(MovieResult movieResult)
    {
        for (var i = 0; i < movieResult.Movies.Count; i++)
        {
            var movie = movieResult.Movies[i];

            this.Output.WriteLine($"""
                - Movie #{i + 1}
                      Title: {movie.Title}
                      Director: {movie.Director}
                      Release year: {movie.ReleaseYear}
                      Rating: {movie.Rating}
                      Genre: {movie.Genre}
                      Is available on streaming: {movie.IsAvailableOnStreaming}
                      Tags: {string.Join(",", movie.Tags ?? [])}
                """);
        }
    }

    /// <summary>Helper method to output <see cref="EmailResult"/> object content.</summary>
    private void OutputResult(EmailResult emailResult)
    {
        for (var i = 0; i < emailResult.Emails.Count; i++)
        {
            var email = emailResult.Emails[i];

            this.Output.WriteLine($"""
                - Email #{i + 1}
                      Body: {email.Body}
                      Category: {email.Category}
                """);
        }
    }

    private void OutputResult(User user)
    {
        this.Output.WriteLine($"""
                - User
                      Name: {user.Name}
                      Email: {user.Email}
                      Age: {user.Age}
                """);
    }

    private Kernel InitializeKernel(bool useGoogleAI)
    {
        Kernel kernel;
        if (useGoogleAI)
        {
            this.Console.WriteLine("============= Google AI - Gemini Chat Completion Structured Outputs =============");

            Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);
            Assert.NotNull(TestConfiguration.GoogleAI.Gemini.ModelId);

            kernel = Kernel.CreateBuilder()
                .AddGoogleAIGeminiChatCompletion(
                    modelId: TestConfiguration.GoogleAI.Gemini.ModelId,
                    apiKey: TestConfiguration.GoogleAI.ApiKey)
                .Build();
        }
        else
        {
            this.Console.WriteLine("============= Vertex AI - Gemini Chat Completion Structured Outputs =============");

            Assert.NotNull(TestConfiguration.VertexAI.ClientId);
            Assert.NotNull(TestConfiguration.VertexAI.ClientSecret);
            Assert.NotNull(TestConfiguration.VertexAI.Location);
            Assert.NotNull(TestConfiguration.VertexAI.ProjectId);
            Assert.NotNull(TestConfiguration.VertexAI.Gemini.ModelId);

            string? bearerToken = TestConfiguration.VertexAI.BearerKey;
            kernel = Kernel.CreateBuilder()
                .AddVertexAIGeminiChatCompletion(
                    modelId: TestConfiguration.VertexAI.Gemini.ModelId,
                    bearerTokenProvider: GetBearerToken,
                    location: TestConfiguration.VertexAI.Location,
                    projectId: TestConfiguration.VertexAI.ProjectId)
                .Build();

            // To generate bearer key, you need installed google sdk or use google web console with command:
            //
            //   gcloud auth print-access-token
            //
            // Above code pass bearer key as string, it is not recommended way in production code,
            // especially if IChatCompletionService will be long lived, tokens generated by google sdk lives for 1 hour.
            // You should use bearer key provider, which will be used to generate token on demand:
            //
            // Example:
            //
            // Kernel kernel = Kernel.CreateBuilder()
            //     .AddVertexAIGeminiChatCompletion(
            //         modelId: TestConfiguration.VertexAI.Gemini.ModelId,
            //         bearerKeyProvider: () =>
            //         {
            //             // This is just example, in production we recommend using Google SDK to generate your BearerKey token.
            //             // This delegate will be called on every request,
            //             // when providing the token consider using caching strategy and refresh token logic when it is expired or close to expiration.
            //             return GetBearerToken();
            //         },
            //         location: TestConfiguration.VertexAI.Location,
            //         projectId: TestConfiguration.VertexAI.ProjectId);

            async ValueTask<string> GetBearerToken()
            {
                if (!string.IsNullOrEmpty(bearerToken))
                {
                    return bearerToken;
                }

                var credential = GoogleWebAuthorizationBroker.AuthorizeAsync(
                    new ClientSecrets
                    {
                        ClientId = TestConfiguration.VertexAI.ClientId,
                        ClientSecret = TestConfiguration.VertexAI.ClientSecret
                    },
                    ["https://www.googleapis.com/auth/cloud-platform"],
                    "user",
                    CancellationToken.None);

                var userCredential = await credential.WaitAsync(CancellationToken.None);
                bearerToken = userCredential.Token.AccessToken;

                return bearerToken;
            }
        }

        return kernel;
    }
    #endregion
}
