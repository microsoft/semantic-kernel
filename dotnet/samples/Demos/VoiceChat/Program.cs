// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel;

internal static class Program
{
    internal static async Task Main(string[] args)
    {
        var builder = Host.CreateApplicationBuilder(args);

        // Adding configuration from appsettings.json and environment variables
        builder.Services.ConfigureOptions<OpenAIOptions>(OpenAIOptions.SectionName);
        builder.Services.ConfigureOptions<ChatOptions>(ChatOptions.SectionName);

        // Configure Semantic Kernel in DI container
        builder.Services
            .AddKernel()
            .AddOpenAIChatCompletion(
                modelId: builder.Configuration[$"{OpenAIOptions.SectionName}:ChatModelId"]!,
                apiKey: builder.Configuration[$"{OpenAIOptions.SectionName}:ApiKey"]!
            );

        // Register audio chat pipeline services
        builder.Services.AddSingleton<AudioPlaybackService>();
        builder.Services.AddSingleton<SpeechToTextService>();
        builder.Services.AddSingleton<TextToSpeechService>();
        builder.Services.AddSingleton<ChatService>();
        builder.Services.AddSingleton<TurnManager>();
        builder.Services.AddSingleton<VadService>();
        builder.Services.AddSingleton<AudioSourceService>();

        // Register audio chat pipeline
        builder.Services.AddTransient<VoiceChatPipeline>();

        using var host = builder.Build();

        // Setting up graceful shutdown on Ctrl+C
        using var cts = new CancellationTokenSource();
        Console.CancelKeyPress += (_, e) =>
        {
            e.Cancel = true;
            cts.Cancel();
        };

        // Run the voice chat pipeline
        using var pipeline = host.Services.GetRequiredService<VoiceChatPipeline>();
        await pipeline.RunAsync(cts.Token);
    }

    private static void ConfigureOptions<TOptions>(this IServiceCollection services, string sectionName) where TOptions : class =>
            services
                .AddOptions<TOptions>()
                .BindConfiguration(sectionName)
                .ValidateDataAnnotations()
                .ValidateOnStart();
}
