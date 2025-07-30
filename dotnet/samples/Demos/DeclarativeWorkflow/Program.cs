// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Reflection;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;

namespace Demo.DeclarativeWorkflow;

internal static class Program
{
    private const string InputEventId = "start-workflow";

    public static async Task Main(string[] args)
    {
        // Load configuration and create kernel with Azure OpenAI Chat Completion service
        IConfiguration config = InitializeConfig();
        // Note: "Kernel" isn't required as part of the new "process framework".
        Kernel kernel = CreateKernel(config["AzureOpenAI:Endpoint"]!, config["AzureOpenAI:ChatDeploymentName"]!);

        Notify("PROCESS INIT\n");

        Stopwatch timer = Stopwatch.StartNew();

        //////////////////////////////////////////////
        // Interpret the workflow YAML into a KernelProcess
        using StreamReader yamlReader = File.OpenText("demo250729.yaml");
        KernelProcess process = ObjectModelBuilder.Build(yamlReader, InputEventId);
        //////////////////////////////////////////////

        Notify($"\nPROCESS DEFINED: {timer.Elapsed}\n");

        Notify("\nPROCESS INVOKE\n");

        //////////////////////////////////////////////
        // Run the process, just like any other KernelProcess
        // NOTE: The pattern here is expected to change in the new "process framework"
        //       (ideally, it will become less complex)
        await using LocalKernelProcessContext context =
            await process.StartAsync(
                kernel,
                new KernelProcessEvent()
                {
                    Id = InputEventId,
                    // Pass the first argument as the input data for the process, if present.
                    Data = args.FirstOrDefault() ?? string.Empty
                });
        //////////////////////////////////////////////

        Notify("\nPROCESS DONE");
    }

    // Load configuration from user-secrets
    private static IConfigurationRoot InitializeConfig() =>
        new ConfigurationBuilder()
            .AddUserSecrets(Assembly.GetExecutingAssembly())
            .Build();

    // Create kernel with Azure OpenAI Chat Completion service
    private static Kernel CreateKernel(string endpoint, string model)
    {
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        kernelBuilder.AddAzureOpenAIChatCompletion(model, endpoint, new AzureCliCredential());

        return kernelBuilder.Build();
    }

    private static void Notify(string message)
    {
        Console.ForegroundColor = ConsoleColor.Cyan;
        try
        {
            Console.WriteLine(message);
        }
        finally
        {
            Console.ResetColor();
        }
    }
}
