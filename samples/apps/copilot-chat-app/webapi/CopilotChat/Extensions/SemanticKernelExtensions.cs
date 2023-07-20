// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using SemanticKernel.Service.CopilotChat.Hubs;
using SemanticKernel.Service.CopilotChat.Options;
using SemanticKernel.Service.CopilotChat.Skills.ChatSkills;
using SemanticKernel.Service.CopilotChat.Storage;
using SemanticKernel.Service.Options;
using SemanticKernel.Service.Services;

namespace SemanticKernel.Service.CopilotChat.Extensions;

/// <summary>
/// Extension methods for registering Copilot Chat components to Semantic Kernel.
/// </summary>
public static class CopilotChatSemanticKernelExtensions
{
    /// <summary>
    /// Add Planner services
    /// </summary>
    public static IServiceCollection AddCopilotChatPlannerServices(this IServiceCollection services)
    {
        IOptions<PlannerOptions>? plannerOptions = services.BuildServiceProvider().GetService<IOptions<PlannerOptions>>();
        services.AddScoped<CopilotChatPlanner>(sp =>
        {
            IKernel plannerKernel = Kernel.Builder
                .WithLogger(sp.GetRequiredService<ILogger<IKernel>>())
                // TODO verify planner has AI service configured
                .WithPlannerBackend(sp.GetRequiredService<IOptions<AIServiceOptions>>().Value)
                .Build();
            return new CopilotChatPlanner(plannerKernel, plannerOptions?.Value);
        });

        // Register Planner skills (AI plugins) here.
        // TODO: Move planner skill registration from ChatController to here.

        return services;
    }

    /// <summary>
    /// Register the Copilot chat skills with the kernel.
    /// </summary>
    public static IKernel RegisterCopilotChatSkills(this IKernel kernel, IServiceProvider sp)
    {
        // Chat skill
        kernel.ImportSkill(new ChatSkill(
                kernel: kernel,
                chatMessageRepository: sp.GetRequiredService<ChatMessageRepository>(),
                chatSessionRepository: sp.GetRequiredService<ChatSessionRepository>(),
                messageRelayHubContext: sp.GetRequiredService<IHubContext<MessageRelayHub>>(),
                promptOptions: sp.GetRequiredService<IOptions<PromptsOptions>>(),
                documentImportOptions: sp.GetRequiredService<IOptions<DocumentMemoryOptions>>(),
                contentModerator: sp.GetRequiredService<AzureContentModerator>(),
                planner: sp.GetRequiredService<CopilotChatPlanner>(),
                logger: sp.GetRequiredService<ILogger<ChatSkill>>()
                ),
            nameof(ChatSkill));

        return kernel;
    }

    /// <summary>
    /// Add the completion backend to the kernel config for the planner.
    /// </summary>
    private static KernelBuilder WithPlannerBackend(this KernelBuilder kernelBuilder, AIServiceOptions options)
    {
        return options.Type switch
        {
            AIServiceOptions.AIServiceType.AzureOpenAI => kernelBuilder.WithAzureChatCompletionService(options.Models.Planner, options.Endpoint, options.Key),
            AIServiceOptions.AIServiceType.OpenAI => kernelBuilder.WithOpenAIChatCompletionService(options.Models.Planner, options.Key),
            _ => throw new ArgumentException($"Invalid {nameof(options.Type)} value in '{AIServiceOptions.PropertyName}' settings."),
        };
    }
}
