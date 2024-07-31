// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

#pragma warning disable SKEXP0001
#pragma warning disable SKEXP0010

namespace AIModelRouter;

internal class Program
{
    private static async Task Main(string[] args)
    {
        var config = new ConfigurationBuilder().AddUserSecrets<Program>().Build();

        var services = new ServiceCollection();
        var builder = services.AddKernel()
            .AddOpenAIChatCompletion(serviceId: "lmstudio", modelId: "phi3", endpoint: new Uri("http://localhost:1234"), apiKey: null)
            .AddOpenAIChatCompletion(serviceId: "ollama", modelId: "phi3", endpoint: new Uri("http://localhost:11434"), apiKey: null)
            .AddOpenAIChatCompletion(serviceId: "openai", modelId: "gpt-4o", apiKey: config["OpenAI:ApiKey"]!);

        builder.Services.AddSingleton<PromptRenderingFilter>();

        var kernel = services.BuildServiceProvider().GetRequiredService<Kernel>();

        //kernel.PromptRenderFilters.Add(new PromptRenderingFilter());
        while (true)
        {
            Console.Write("\n\nEnter your message to AI: ");
            var userMessage = Console.ReadLine();

            if (string.IsNullOrWhiteSpace(userMessage)) { return; }
            var arguments = new KernelArguments()
            {
                ExecutionSettings = new Dictionary<string, PromptExecutionSettings>() { { new Router().FindService(userMessage),
                new OpenAIPromptExecutionSettings() { ResponseFormat = "json" } } }
            };

            Console.Write("\n\nAI response: ");

            await foreach (var chatChunk in kernel.InvokePromptStreamingAsync(userMessage, arguments).ConfigureAwait(false))
            {
                Console.Write(chatChunk);
            }
        }
    }

    public class Router()
    {
        public string FindService(string prompt)
        {
            if (Contains(prompt, "ollama")) { return "ollama"; }
            else if (Contains(prompt, "openai")) { return "openai"; }
            return "lmstudio";
        }

        private static bool Contains(string prompt, string pattern)
        {
#pragma warning disable CA2249 // Consider using 'string.Contains' instead of 'string.IndexOf'
            return prompt.IndexOf(pattern, StringComparison.CurrentCultureIgnoreCase) >= 0;
#pragma warning restore CA2249 // Consider using 'string.Contains' instead of 'string.IndexOf'
        }
    }

    public class PromptRenderingFilter : IPromptRenderFilter
    {
        public Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            Console.WriteLine($"Rendering prompt for service '{context.Arguments.ExecutionSettings?.FirstOrDefault().Key}'");
            return next(context);
        }
    }
}
