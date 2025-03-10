// Copyright (c) Microsoft. All rights reserved.
using System.Reflection;
using System.Text;
using System.Text.Json;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

public abstract class BaseTest : TextWriter
{
    /// <summary>
    /// Flag to force usage of OpenAI configuration if both <see cref="TestConfiguration.OpenAI"/>
    /// and <see cref="TestConfiguration.AzureOpenAI"/> are defined.
    /// If 'false', Azure takes precedence.
    /// </summary>
    protected virtual bool ForceOpenAI { get; } = false;

    protected ITestOutputHelper Output { get; }

    protected ILoggerFactory LoggerFactory { get; }

    /// <summary>
    /// This property makes the samples Console friendly. Allowing them to be copied and pasted into a Console app, with minimal changes.
    /// </summary>
    public BaseTest Console => this;

    protected bool UseOpenAIConfig => this.ForceOpenAI || string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint);

    protected string? ApiKey =>
        this.UseOpenAIConfig ?
            TestConfiguration.OpenAI.ApiKey :
            TestConfiguration.AzureOpenAI.ApiKey;

    protected string? Endpoint => UseOpenAIConfig ? null : TestConfiguration.AzureOpenAI.Endpoint;

    protected string Model =>
        this.UseOpenAIConfig ?
            TestConfiguration.OpenAI.ChatModelId :
            TestConfiguration.AzureOpenAI.ChatDeploymentName;

    /// <summary>
    /// Returns true if the test configuration has a valid Bing API key.
    /// </summary>
    protected bool UseBingSearch => TestConfiguration.Bing.ApiKey is not null;

    protected Kernel CreateKernelWithChatCompletion()
    {
        var builder = Kernel.CreateBuilder();

        AddChatCompletionToKernel(builder);

        return builder.Build();
    }

    protected void AddChatCompletionToKernel(IKernelBuilder builder)
    {
        if (this.UseOpenAIConfig)
        {
            builder.AddOpenAIChatCompletion(
                TestConfiguration.OpenAI.ChatModelId,
                TestConfiguration.OpenAI.ApiKey);
        }
        else if (!string.IsNullOrEmpty(this.ApiKey))
        {
            builder.AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);
        }
        else
        {
            builder.AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                new AzureCliCredential());
        }
    }

    protected BaseTest(ITestOutputHelper output, bool redirectSystemConsoleOutput = false)
    {
        this.Output = output;
        this.LoggerFactory = new XunitLogger(output);

        IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddJsonFile("appsettings.Development.json", true)
            .AddEnvironmentVariables()
            .AddUserSecrets(Assembly.GetExecutingAssembly())
            .Build();

        TestConfiguration.Initialize(configRoot);

        // Redirect System.Console output to the test output if requested
        if (redirectSystemConsoleOutput)
        {
            System.Console.SetOut(this);
        }
    }

    /// <inheritdoc/>
    public override void WriteLine(object? value = null)
        => this.Output.WriteLine(value ?? string.Empty);

    /// <inheritdoc/>
    public override void WriteLine(string? format, params object?[] arg)
        => this.Output.WriteLine(format ?? string.Empty, arg);

    /// <inheritdoc/>
    public override void WriteLine(string? value)
        => this.Output.WriteLine(value ?? string.Empty);

    /// <inheritdoc/>
    /// <remarks>
    /// <see cref="ITestOutputHelper"/> only supports output that ends with a newline.
    /// User this method will resolve in a call to <see cref="WriteLine(string?)"/>.
    /// </remarks>
    public override void Write(object? value = null)
        => this.Output.WriteLine(value ?? string.Empty);

    /// <inheritdoc/>
    /// <remarks>
    /// <see cref="ITestOutputHelper"/> only supports output that ends with a newline.
    /// User this method will resolve in a call to <see cref="WriteLine(string?)"/>.
    /// </remarks>
    public override void Write(char[]? buffer)
        => this.Output.WriteLine(new string(buffer));

    /// <inheritdoc/>
    public override Encoding Encoding => Encoding.UTF8;

    /// <summary>
    /// Outputs the last message in the chat history.
    /// </summary>
    /// <param name="chatHistory">Chat history</param>
    protected void OutputLastMessage(ChatHistory chatHistory)
    {
        var message = chatHistory.Last();

        Console.WriteLine($"{message.Role}: {message.Content}");
        Console.WriteLine("------------------------");
    }

    /// <summary>
    /// Outputs out the stream of generated message tokens.
    /// </summary>
    protected async Task StreamMessageOutputAsync(IChatCompletionService chatCompletionService, ChatHistory chatHistory, AuthorRole authorRole)
    {
        bool roleWritten = false;
        string fullMessage = string.Empty;

        await foreach (var chatUpdate in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            if (!roleWritten && chatUpdate.Role.HasValue)
            {
                Console.Write($"{chatUpdate.Role.Value}: {chatUpdate.Content}");
                roleWritten = true;
            }

            if (chatUpdate.Content is { Length: > 0 })
            {
                fullMessage += chatUpdate.Content;
                Console.Write(chatUpdate.Content);
            }
        }

        Console.WriteLine("\n------------------------");
        chatHistory.AddMessage(authorRole, fullMessage);
    }

    /// <summary>
    /// Utility method to write a horizontal rule to the console.
    /// </summary>
    protected void WriteHorizontalRule()
        => Console.WriteLine(new string('-', HorizontalRuleLength));

    protected sealed class LoggingHandler(HttpMessageHandler innerHandler, ITestOutputHelper output) : DelegatingHandler(innerHandler)
    {
        private static readonly JsonSerializerOptions s_jsonSerializerOptions = new() { WriteIndented = true };

        private readonly ITestOutputHelper _output = output;

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // Log the request details
            if (request.Content is not null)
            {
                var content = await request.Content.ReadAsStringAsync(cancellationToken);
                this._output.WriteLine("=== REQUEST ===");
                try
                {
                    string formattedContent = JsonSerializer.Serialize(JsonSerializer.Deserialize<JsonElement>(content), s_jsonSerializerOptions);
                    this._output.WriteLine(formattedContent);
                }
                catch (JsonException)
                {
                    this._output.WriteLine(content);
                }
                this._output.WriteLine(string.Empty);
            }

            // Call the next handler in the pipeline
            var response = await base.SendAsync(request, cancellationToken);

            if (response.Content is not null)
            {
                // Log the response details
                var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);
                this._output.WriteLine("=== RESPONSE ===");
                this._output.WriteLine(responseContent);
                this._output.WriteLine(string.Empty);
            }

            return response;
        }
    }

    #region private
    private const int HorizontalRuleLength = 80;
    #endregion
}
