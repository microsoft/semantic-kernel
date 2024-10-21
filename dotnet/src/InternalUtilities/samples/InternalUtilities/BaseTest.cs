<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
using System.Reflection;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
﻿// Copyright (c) Microsoft. All rights reserved.
using System.Reflection;
=======
// Copyright (c) Microsoft. All rights reserved.
using System.Reflection;
using System.Text;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
using System.Reflection;
using System.Text;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
// Copyright (c) Microsoft. All rights reserved.
using System.Reflection;
using System.Text;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
public abstract class BaseTest
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
public abstract class BaseTest
=======
public abstract class BaseTest : TextWriter
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
public abstract class BaseTest : TextWriter
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
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
        else
        {
            builder.AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);
        }
    }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    protected BaseTest(ITestOutputHelper output)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    protected BaseTest(ITestOutputHelper output)
=======
    protected BaseTest(ITestOutputHelper output, bool redirectSystemConsoleOutput = false)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    protected BaseTest(ITestOutputHelper output, bool redirectSystemConsoleOutput = false)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    {
        this.Output = output;
        this.LoggerFactory = new XunitLogger(output);

        IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddJsonFile("appsettings.Development.json", true)
            .AddEnvironmentVariables()
            .AddUserSecrets(Assembly.GetExecutingAssembly())
            .Build();

        TestConfiguration.Initialize(configRoot);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    }

    /// <summary>
    /// This method can be substituted by Console.WriteLine when used in Console apps.
    /// </summary>
    /// <param name="target">Target object to write</param>
    public void WriteLine(object? target = null)
        => this.Output.WriteLine(target ?? string.Empty);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

        // Redirect System.Console output to the test output if requested
        if (redirectSystemConsoleOutput)
        {
            System.Console.SetOut(this);
        }
    }

    /// <inheritdoc/>
    public override void WriteLine(object? value = null)
        => this.Output.WriteLine(value ?? string.Empty);
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

    /// <summary>
    /// This method can be substituted by Console.WriteLine when used in Console apps.
    /// </summary>
    /// <param name="format">Format string</param>
    /// <param name="args">Arguments</param>
    public void WriteLine(string? format, params object?[] args)
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        => this.Output.WriteLine(format ?? string.Empty, args);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        => this.Output.WriteLine(format ?? string.Empty, args);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        => this.Output.WriteLine(format ?? string.Empty, args);
=======
>>>>>>> Stashed changes
=======
        => this.Output.WriteLine(format ?? string.Empty, args);
=======
>>>>>>> Stashed changes
>>>>>>> head
    {
        if (args is null || args.Length == 0)
        {
            this.Output.WriteLine(format ?? string.Empty);
        }
        else
        {
            this.Output.WriteLine(format ?? string.Empty, args);
        }
    }
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

    /// <summary>
    /// This method can be substituted by Console.WriteLine when used in Console apps.
    /// </summary>
    /// <param name="message">The message</param>
public void WriteLine(string? message = null)
    => this.Output.WriteLine(message ?? string.Empty);
        => this.Output.WriteLine(message ?? string.Empty);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    /// <summary>
    /// Current interface ITestOutputHelper does not have a Write method. This extension method adds it to make it analogous to Console.Write when used in Console apps.
    /// </summary>
    /// <param name="target">Target object to write</param>
    public void Write(object? target = null)
        => this.Output.WriteLine(target ?? string.Empty);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

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
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

    /// <summary>
    /// Utility method to write a horizontal rule to the console.
    /// </summary>
    protected void WriteHorizontalRule()
        => Console.WriteLine(new string('-', HorizontalRuleLength));

<<<<<<< main
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> div
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
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
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

    #region private
    private const int HorizontalRuleLength = 80;
    #endregion
<<<<<<< main
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> div
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
}
