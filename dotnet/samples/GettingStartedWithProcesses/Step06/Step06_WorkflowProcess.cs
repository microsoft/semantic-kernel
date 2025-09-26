// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Step06;

public class Step06_WorkflowProcess : BaseTest
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    public Step06_WorkflowProcess(ITestOutputHelper output)
        : base(output, redirectSystemConsoleOutput: true) { }

    [Theory]
    [InlineData("deepResearch")]
    [InlineData("demo250729")]
    [InlineData("testChat")]
    [InlineData("testCondition")]
    [InlineData("testEnd")]
    [InlineData("testExpression")]
    [InlineData("testGoto")]
    [InlineData("testLoop")]
    [InlineData("testLoopBreak")]
    [InlineData("testLoopContinue")]
    [InlineData("testTopic")]
    public async Task RunWorkflow(string fileName)
    {
        using InterceptHandler customHandler = new();
        using HttpClient customClient = new(customHandler, disposeHandler: false);

        const string InputEventId = "question";

        Console.WriteLine("PROCESS INIT\n");

        using StreamReader yamlReader = File.OpenText(@$"{nameof(Step06)}\{fileName}.yaml");
        WorkflowContext workflowContext =
            new()
            {
                HttpClient = customClient,
                LoggerFactory = this.LoggerFactory,
                ActivityChannel = this.Console,
                ProjectEndpoint = TestConfiguration.AzureAI.Endpoint,
                ProjectCredentials = new AzureCliCredential(),
            };
        KernelProcess process = ObjectModelBuilder.Build(yamlReader, InputEventId, workflowContext);

        Console.WriteLine("\nPROCESS INVOKE\n");

        Kernel kernel = this.CreateKernel(customClient);
        IChatCompletionService chatService = kernel.GetRequiredService<IChatCompletionService>();
        await using LocalKernelProcessContext context = await process.StartAsync(kernel, new KernelProcessEvent() { Id = InputEventId, Data = "<placeholder>" });
        Console.WriteLine("\nPROCESS DONE");
    }

    private Kernel CreateKernel(HttpClient httpClient, bool withLogger = false)
    {
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        if (withLogger)
        {
            kernelBuilder.Services.AddSingleton(this.LoggerFactory);
        }

        kernelBuilder.AddAzureOpenAIChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            new AzureCliCredential(),
            httpClient: httpClient);

        return kernelBuilder.Build();
    }
}

internal sealed class InterceptHandler : HttpClientHandler
{
    private static readonly JsonSerializerOptions s_options = new() { WriteIndented = true };

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        // Call the inner handler to process the request and get the response
        HttpResponseMessage response = await base.SendAsync(request, cancellationToken);

        // Intercept and modify the response
        Console.WriteLine($"{request.Method} {request.RequestUri}");
        if (response.Content != null)
        {
            string responseContent;
            try
            {
                JsonDocument responseDocument = await JsonDocument.ParseAsync(await response.Content.ReadAsStreamAsync(cancellationToken), cancellationToken: cancellationToken);
                responseContent = JsonSerializer.Serialize(responseDocument, s_options);
            }
            catch (ArgumentException)
            {
                responseContent = await response.Content.ReadAsStringAsync(cancellationToken);
            }
            catch (JsonException)
            {
                responseContent = await response.Content.ReadAsStringAsync(cancellationToken);
            }
            response.Content = new StringContent(responseContent);
            //Console.WriteLine(responseContent); // %%% RAISE EVENT
        }

        return response;
    }
}
