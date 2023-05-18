// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using SemanticKernel.Service.CopilotChat.Options;
using SemanticKernel.Service.CopilotChat.Skills.ChatSkills;
using SemanticKernel.Service.CopilotChat.Storage;
using SemanticKernel.Service.Options;

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
        if (plannerOptions != null && plannerOptions.Value.Enabled)
        {
            services.AddScoped<CopilotChatPlanner>(sp => new CopilotChatPlanner(Kernel.Builder
                .WithLogger(sp.GetRequiredService<ILogger<IKernel>>())
                .WithConfiguration(
                    new KernelConfig().AddPlannerBackend(
                        sp.GetRequiredService<IOptions<PlannerOptions>>().Value.AIService!)
                ) // TODO verify planner has AI service configured
                .Build()));

            // Register Planner skills (AI plugins) here.
            // TODO: Move planner skill registration from ChatController to here.
        }

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
                promptOptions: sp.GetRequiredService<IOptions<PromptsOptions>>(),
                planner: sp.GetRequiredService<CopilotChatPlanner>(),
                plannerOptions: sp.GetRequiredService<IOptions<PlannerOptions>>().Value,
                logger: sp.GetRequiredService<ILogger<ChatSkill>>()),
            nameof(ChatSkill));

        // Document memory skill
        kernel.ImportSkill(new DocumentMemorySkill(
                sp.GetRequiredService<IOptions<PromptsOptions>>(),
                sp.GetRequiredService<IOptions<DocumentMemoryOptions>>().Value),
            nameof(DocumentMemorySkill));

        return kernel;
    }

    /// <summary>
    /// Add the completion backend to the kernel config for the planner.
    /// </summary>
    private static KernelConfig AddPlannerBackend(this KernelConfig kernelConfig, AIServiceOptions options)
    {
        switch (options.AIService)
        {
            case AIServiceOptions.AIServiceType.AzureOpenAI:
                kernelConfig.AddAzureChatCompletionService(
                    deploymentName: options.DeploymentOrModelId,
                    endpoint: options.Endpoint,
                    apiKey: options.Key);
                break;

            case AIServiceOptions.AIServiceType.OpenAI:
                kernelConfig.AddOpenAIChatCompletionService(
                    modelId: options.DeploymentOrModelId,
                    apiKey: options.Key);
                break;

            default:
                throw new ArgumentException($"Invalid {nameof(options.AIService)} value in '{AIServiceOptions.CompletionPropertyName}' settings.");
        }

        return kernelConfig;
    }
}
