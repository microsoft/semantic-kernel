// Copyright (c) Microsoft. All rights reserved.

using FunctionInvocationApproval.Options;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace FunctionInvocationApproval;

internal sealed class Program
{
    /// <summary>
    /// This console application shows how to use function invocation filter to invoke function only if such operation was approved.
    /// If function invocation was rejected, the result will contain an information about this, so LLM can react accordingly.
    /// Application uses a plugin that allows to build a software by following main development stages:
    /// Collection of requirements, design, implementation, testing and deployment.
    /// Each step can be approved or rejected. Based on that, LLM will decide how to proceed.
    /// </summary>
    public static async Task Main()
    {
        var builder = Kernel.CreateBuilder();

        // Add LLM configuration
        AddChatCompletion(builder);

        // Add function approval service and filter
        builder.Services.AddSingleton<IFunctionApprovalService, ConsoleFunctionApprovalService>();
        builder.Services.AddSingleton<IFunctionInvocationFilter, FunctionInvocationFilter>();

        // Add software builder plugin
        builder.Plugins.AddFromType<SoftwareBuilderPlugin>();

        var kernel = builder.Build();

        // Enable automatic function calling
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            Temperature = 0,
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        };

        // Initialize kernel arguments.
        var arguments = new KernelArguments(executionSettings);

        // Start execution
        // Try to reject invocation at each stage to compare LLM results.
        var result = await kernel.InvokePromptAsync("I want to build a software. Let's start from the first step.", arguments);

        Console.WriteLine(result);
    }

    #region Plugins

    public sealed class SoftwareBuilderPlugin
    {
        [KernelFunction]
        public string CollectRequirements()
        {
            Console.WriteLine("Collecting requirements...");
            return "Requirements";
        }

        [KernelFunction]
        public string Design(string requirements)
        {
            Console.WriteLine($"Designing based on: {requirements}");
            return "Design";
        }

        [KernelFunction]
        public string Implement(string requirements, string design)
        {
            Console.WriteLine($"Implementing based on {requirements} and {design}");
            return "Implementation";
        }

        [KernelFunction]
        public string Test(string requirements, string design, string implementation)
        {
            Console.WriteLine($"Testing based on {requirements}, {design} and {implementation}");
            return "Test Results";
        }

        [KernelFunction]
        public string Deploy(string requirements, string design, string implementation, string testResults)
        {
            Console.WriteLine($"Deploying based on {requirements}, {design}, {implementation} and {testResults}");
            return "Deployment";
        }
    }

    #endregion

    #region Approval

    /// <summary>
    /// Service that verifies if function invocation is approved.
    /// </summary>
    public interface IFunctionApprovalService
    {
        bool IsInvocationApproved(KernelFunction function, KernelArguments arguments);
    }

    /// <summary>
    /// Service that verifies if function invocation is approved using console.
    /// </summary>
    public sealed class ConsoleFunctionApprovalService : IFunctionApprovalService
    {
        public bool IsInvocationApproved(KernelFunction function, KernelArguments arguments)
        {
            Console.WriteLine("====================");
            Console.WriteLine($"Function name: {function.Name}");
            Console.WriteLine($"Plugin name: {function.PluginName ?? "N/A"}");

            if (arguments.Count == 0)
            {
                Console.WriteLine("\nArguments: N/A");
            }
            else
            {
                Console.WriteLine("\nArguments:");

                foreach (var argument in arguments)
                {
                    Console.WriteLine($"{argument.Key}: {argument.Value}");
                }
            }

            Console.WriteLine("\nApprove invocation? (yes/no)");

            var input = Console.ReadLine();

            return input?.Equals("yes", StringComparison.OrdinalIgnoreCase) ?? false;
        }
    }

    #endregion

    #region Filter

    /// <summary>
    /// Filter to invoke function only if it's approved.
    /// </summary>
    public sealed class FunctionInvocationFilter(IFunctionApprovalService approvalService) : IFunctionInvocationFilter
    {
        private readonly IFunctionApprovalService _approvalService = approvalService;

        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            // Invoke the function only if it's approved.
            if (this._approvalService.IsInvocationApproved(context.Function, context.Arguments))
            {
                await next(context);
            }
            else
            {
                // Otherwise, return a result that operation was rejected.
                context.Result = new FunctionResult(context.Result, "Operation was rejected.");
            }
        }
    }

    #endregion

    #region Configuration

    private static void AddChatCompletion(IKernelBuilder builder)
    {
        // Get configuration
        var config = new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build();

        var openAIOptions = config.GetSection(OpenAIOptions.SectionName).Get<OpenAIOptions>();
        var azureOpenAIOptions = config.GetSection(AzureOpenAIOptions.SectionName).Get<AzureOpenAIOptions>();

        if (openAIOptions is not null && openAIOptions.IsValid)
        {
            builder.AddOpenAIChatCompletion(openAIOptions.ChatModelId, openAIOptions.ApiKey);
        }
        else if (azureOpenAIOptions is not null && azureOpenAIOptions.IsValid)
        {
            builder.AddAzureOpenAIChatCompletion(
                azureOpenAIOptions.ChatDeploymentName,
                azureOpenAIOptions.Endpoint,
                azureOpenAIOptions.ApiKey);
        }
        else
        {
            throw new Exception("OpenAI/Azure OpenAI configuration was not found.");
        }
    }

    #endregion
}
