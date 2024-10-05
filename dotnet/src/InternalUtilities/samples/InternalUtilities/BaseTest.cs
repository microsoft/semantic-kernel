// Copyright (c) Microsoft. All rights reserved.
using System.Reflection;
using System.Text;
using System.Text.Json;
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

    protected string ApiKey =>
        this.UseOpenAIConfig ?
            TestConfiguration.OpenAI.ApiKey :
            TestConfiguration.AzureOpenAI.ApiKey;

    protected string? Endpoint => UseOpenAIConfig ? null : TestConfiguration.AzureOpenAI.Endpoint;

    protected string Model =>
        this.UseOpenAIConfig ?
            TestConfiguration.OpenAI.ChatModelId :
            TestConfiguration.AzureOpenAI.ChatDeploymentName;

    protected Kernel CreateKernelWithChatCompletion()
    {
        var builder = Kernel.CreateBuilder();

        if (this.UseOpenAIConfig)
        {
            builder.AddOpenAIChatCompletion(
                TestConfiguration.OpenAI.ChatModelId,
                TestConfiguration.OpenAI.ApiKey);
        }
        else
        {
            builder.AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);
        }

        return builder.Build();
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
    public override void Write(object? value = null)
        => this.Output.WriteLine(value ?? string.Empty);

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
}
