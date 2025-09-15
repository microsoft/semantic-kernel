// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Filtering;

/// <summary>
/// This sample shows how to switch between Azure OpenAI deployments based on the functions that are being called.
/// This can be useful if semantic caching is enabled and you want to switch to a different deployment based on the functions that are being called.
/// </summary>
public class AzureOpenAI_DeploymentSwitch(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task DeploymentSwitchAsync()
    {
        Assert.NotNull(TestConfiguration.AzureOpenAI.ChatDeploymentName);
        Assert.NotNull(TestConfiguration.AzureOpenAI.Endpoint);

        // Create a logging handler to output HTTP requests and responses
        using var httpHandler = new HttpClientHandler();
        using var loggingHandler = new LoggingHandler(httpHandler, this.Output);
        using var httpClient = new HttpClient(loggingHandler);

        // Create KernelBuilder with an auto function invocation filter
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoFunctionInvocationFilter(this.Output));

        // Define the endpoints for the two Azure OpenAI services
        var endpoint1 = "https://contoso-eastus.openai.azure.com/";
        var endpoint2 = "https://contoso-swedencentral.openai.azure.com/";

        // Add Azure OpenAI chat completion services
        kernelBuilder.AddAzureOpenAIChatCompletion(
            serviceId: "eastus",
            deploymentName: "gpt-4o-mini",
            endpoint: endpoint1,
            credentials: new AzureCliCredential(),
            httpClient: httpClient,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);
        kernelBuilder.AddAzureOpenAIChatCompletion(
            serviceId: "swedencentral",
            deploymentName: "gpt-4o",
            endpoint: endpoint2,
            credentials: new AzureCliCredential(),
            httpClient: httpClient,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);

        var kernel = kernelBuilder.Build();

        kernel.ImportPluginFromFunctions("HelperFunctions",
        [
            kernel.CreateFunctionFromMethod(() => "Brown", "GetEyeColor", "Retrieves eye color for the current user."),
            kernel.CreateFunctionFromMethod(() => DateTime.UtcNow.ToString("R"), "GetCurrentDateTimeInUtc", "Retrieves the current date time in UTC."),
        ]);

        OpenAIPromptExecutionSettings settings = new()
        {
            ServiceId = "swedencentral",
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        var reply = await kernel.InvokePromptAsync("What time is it and what is my eye color and what time is it?", new(settings));

        Console.WriteLine(reply);
    }

    private sealed class AutoFunctionInvocationFilter(ITestOutputHelper output) : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            var kernel = context.Kernel;
            var chatHistory = context.ChatHistory;
            var executionSettings = context.ExecutionSettings;
            var functionCalls = FunctionCallContent.GetFunctionCalls(context.ChatHistory.Last());

            if (executionSettings is not null && "swedencentral".Equals(executionSettings.ServiceId, StringComparison.Ordinal))
            {
                bool includesGetEyeColor = functionCalls.Any(fc => fc.FunctionName.Equals("GetEyeColor", StringComparison.Ordinal));

                // For the "GetEyeColor" function, switch to a different deployment. 
                // If the function is not present in the collection of function calls, proceed with the request as usual.
                if (!includesGetEyeColor)
                {
                    await next(context);
                }
                else
                {
                    output.WriteLine("Switching to use eastus deployment");

                    chatHistory.RemoveAt(chatHistory.Count - 1);

                    IChatCompletionService chatCompletionService = kernel.Services.GetRequiredKeyedService<IChatCompletionService>("eastus");

                    OpenAIPromptExecutionSettings settings = new()
                    {
                        ServiceId = "eastus",
                        FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
                    };

                    var chatContent = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, context.Kernel);

                    context.Result = new FunctionResult(context.Result, chatContent);
                    context.Terminate = true;
                }
            }
            else
            {
                await next(context);
            }
        }
    }
}
