// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.ClientModel.Primitives;
using System.Net;
using System.Runtime.CompilerServices;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;

namespace ChatCompletion;

/// <summary>
/// This example demonstrates how an AI application can use code to attempt inference with the first available chat client in the list, falling back to the next client if the previous one fails.
/// The <see cref="FallbackChatClient"/> class handles all the fallback complexities, abstracting them away from the application code.
/// Since the <see cref="FallbackChatClient"/> class implements the <see cref="IChatClient"/> interface, the chat client used for inference the application can be easily replaced with the <see cref="FallbackChatClient"/>.
/// </summary>
/// <remarks>
/// The <see cref="FallbackChatClient"/> class is useful when an application utilizes multiple models and needs to switch between them based on the situation.
/// For example, the application may use a cloud-based model by default and seamlessly fall back to a local model when the cloud model is unavailable (e.g., in offline mode), and vice versa.
/// Additionally, the application can enhance resilience by employing several cloud models, falling back to the next one if the previous model fails.
/// </remarks>
public class HybridCompletion_Fallback(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This example demonstrates how to perform completion using the <see cref="FallbackChatClient"/>, which falls back to an available model when the primary model is unavailable.
    /// </summary>
    [Fact]
    public async Task FallbackToAvailableModelAsync()
    {
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        // Create and register an unavailable chat client that fails with 503 Service Unavailable HTTP status code
        kernelBuilder.Services.AddSingleton<IChatClient>(CreateUnavailableOpenAIChatClient());

        // Create and register a cloud available chat client
        kernelBuilder.Services.AddSingleton<IChatClient>(CreateAzureOpenAIChatClient());

        // Create and register fallback chat client that will fallback to the available chat client when unavailable chat client fails
        kernelBuilder.Services.AddSingleton<IChatCompletionService>((sp) =>
        {
            IEnumerable<IChatClient> chatClients = sp.GetServices<IChatClient>();

            return new FallbackChatClient(chatClients.ToList()).AsChatCompletionService();
        });

        Kernel kernel = kernelBuilder.Build();
        kernel.ImportPluginFromFunctions("Weather", [KernelFunctionFactory.CreateFromMethod(() => "It's sunny", "GetWeather")]);

        AzureOpenAIPromptExecutionSettings settings = new()
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        FunctionResult result = await kernel.InvokePromptAsync("Do I need an umbrella?", new(settings));

        Output.WriteLine(result);
    }

    /// <summary>
    /// This example demonstrates how to perform streaming completion using the <see cref="FallbackChatClient"/>, which falls back to an available model when the primary model is unavailable.
    /// </summary>
    [Fact]
    public async Task FallbackToAvailableModelStreamingAsync()
    {
        // Create an unavailable chat client that fails with 503 Service Unavailable HTTP status code
        IChatClient unavailableChatClient = CreateUnavailableOpenAIChatClient();

        // Create a cloud available chat client
        IChatClient availableChatClient = CreateAzureOpenAIChatClient();

        // Create a fallback chat client that will fallback to the available chat client when unavailable chat client fails
        IChatCompletionService fallbackCompletionService = new FallbackChatClient([unavailableChatClient, availableChatClient]).AsChatCompletionService();

        Kernel kernel = new();
        kernel.ImportPluginFromFunctions("Weather", [KernelFunctionFactory.CreateFromMethod(() => "It's sunny", "GetWeather")]);

        AzureOpenAIPromptExecutionSettings settings = new()
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        IAsyncEnumerable<StreamingChatMessageContent> result = fallbackCompletionService.GetStreamingChatMessageContentsAsync("Do I need an umbrella?", settings, kernel);

        await foreach (var update in result)
        {
            Output.WriteLine(update);
        }
    }

    private static IChatClient CreateUnavailableOpenAIChatClient()
    {
        AzureOpenAIClientOptions options = new()
        {
            Transport = new HttpClientPipelineTransport(
                new HttpClient
                (
                    new StubHandler(new HttpClientHandler(), async (response) => { response.StatusCode = System.Net.HttpStatusCode.ServiceUnavailable; })
                )
            )
        };

        IChatClient openAiClient = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAI.Endpoint), new AzureCliCredential(), options).GetChatClient(TestConfiguration.AzureOpenAI.ChatDeploymentName).AsIChatClient();

        return new ChatClientBuilder(openAiClient)
            .UseFunctionInvocation()
            .Build();
    }

    private static IChatClient CreateAzureOpenAIChatClient()
    {
        IChatClient chatClient = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAI.Endpoint), new AzureCliCredential()).GetChatClient(TestConfiguration.AzureOpenAI.ChatDeploymentName).AsIChatClient();

        return new ChatClientBuilder(chatClient)
            .UseFunctionInvocation()
            .Build();
    }

    protected sealed class StubHandler(HttpMessageHandler innerHandler, Func<HttpResponseMessage, Task> handler) : DelegatingHandler(innerHandler)
    {
        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var result = await base.SendAsync(request, cancellationToken);

            await handler(result);

            return result;
        }
    }
}

/// <summary>
/// Represents a chat client that performs inference using the first available chat client in the list, falling back to the next one if the previous client fails.
/// </summary>
internal sealed class FallbackChatClient : IChatClient
{
    private readonly IList<IChatClient> _chatClients;
    private static readonly List<HttpStatusCode> s_defaultFallbackStatusCodes = new()
    {
        HttpStatusCode.InternalServerError,
        HttpStatusCode.NotImplemented,
        HttpStatusCode.BadGateway,
        HttpStatusCode.ServiceUnavailable,
        HttpStatusCode.GatewayTimeout
    };

    /// <summary>
    /// Initializes a new instance of the <see cref="FallbackChatClient"/> class.
    /// </summary>
    /// <param name="chatClients">The chat clients to fallback to.</param>
    public FallbackChatClient(IList<IChatClient> chatClients)
    {
        this._chatClients = chatClients?.Any() == true ? chatClients : throw new ArgumentException("At least one chat client must be provided.", nameof(chatClients));
    }

    /// <summary>
    /// Gets or sets the HTTP status codes that will trigger the fallback to the next chat client.
    /// </summary>
    public List<HttpStatusCode>? FallbackStatusCodes { get; set; }

    /// <inheritdoc/>
    public ChatClientMetadata Metadata => new();

    /// <inheritdoc/>
    public async Task<Microsoft.Extensions.AI.ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        for (int i = 0; i < this._chatClients.Count; i++)
        {
            var chatClient = this._chatClients.ElementAt(i);

            try
            {
                return await chatClient.GetResponseAsync(messages, options, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                if (this.ShouldFallbackToNextClient(ex, i, this._chatClients.Count))
                {
                    continue;
                }

                throw;
            }
        }

        // If all clients fail, throw an exception or return a default value
        throw new InvalidOperationException("Neither of the chat clients could complete the inference.");
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        for (int i = 0; i < this._chatClients.Count; i++)
        {
            var chatClient = this._chatClients.ElementAt(i);

            IAsyncEnumerable<ChatResponseUpdate> completionStream = chatClient.GetStreamingResponseAsync(messages, options, cancellationToken);

            ConfiguredCancelableAsyncEnumerable<ChatResponseUpdate>.Enumerator enumerator = completionStream.ConfigureAwait(false).GetAsyncEnumerator();

            try
            {
                try
                {
                    // Move to the first update to reveal any exceptions.
                    if (!await enumerator.MoveNextAsync())
                    {
                        yield break;
                    }
                }
                catch (Exception ex)
                {
                    if (this.ShouldFallbackToNextClient(ex, i, this._chatClients.Count))
                    {
                        continue;
                    }

                    throw;
                }

                // Yield the first update.
                yield return enumerator.Current;

                // Yield the rest of the updates.
                while (await enumerator.MoveNextAsync())
                {
                    yield return enumerator.Current;
                }

                // The stream has ended so break the while loop.
                break;
            }
            finally
            {
                await enumerator.DisposeAsync();
            }
        }
    }

    private bool ShouldFallbackToNextClient(Exception ex, int clientIndex, int numberOfClients)
    {
        // If the exception is thrown by the last client then don't fallback.
        if (clientIndex == numberOfClients - 1)
        {
            return false;
        }

        HttpStatusCode? statusCode = ex switch
        {
            HttpOperationException operationException => operationException.StatusCode,
            HttpRequestException httpRequestException => httpRequestException.StatusCode,
            ClientResultException clientResultException => (HttpStatusCode?)clientResultException.Status,
            _ => throw new InvalidOperationException($"Unsupported exception type: {ex.GetType()}."),
        };

        if (statusCode is null)
        {
            throw new InvalidOperationException("The exception does not contain an HTTP status code.");
        }

        return (this.FallbackStatusCodes ?? s_defaultFallbackStatusCodes).Contains(statusCode!.Value);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        // We don't own the chat clients so we don't dispose them.
    }

    /// <inheritdoc/>
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        return null;
    }
}
