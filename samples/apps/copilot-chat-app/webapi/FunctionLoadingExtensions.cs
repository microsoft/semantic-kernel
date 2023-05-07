// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.TemplateEngine;
using SemanticKernel.Service.Config;
using SemanticKernel.Service.Skills;
using SemanticKernel.Service.Storage;

namespace SemanticKernel.Service;

internal static class FunctionLoadingExtensions
{
    /// <summary>
    /// Register local semantic skills with the kernel.
    /// </summary>
    internal static void RegisterSemanticSkills(
        this IKernel kernel,
        string skillsDirectory,
        ILogger logger)
    {
        string[] subDirectories = Directory.GetDirectories(skillsDirectory);

        foreach (string subDir in subDirectories)
        {
            try
            {
                kernel.ImportSemanticSkillFromDirectory(skillsDirectory, Path.GetFileName(subDir)!);
            }
            catch (TemplateException e)
            {
                logger.LogError("Could not load skill from {Directory}: {Message}", subDir, e.Message);
            }
        }
    }

    /// <summary>
    /// Register native skills with the kernel.
    /// </summary>
    internal static void RegisterNativeSkills(
        this IKernel kernel,
        ChatSessionRepository chatSessionRepository,
        ChatMessageRepository chatMessageRepository,
        PromptSettings promptSettings,
        CopilotChatPlanner planner,
        PlannerOptions plannerOptions,
        DocumentMemoryOptions documentMemoryOptions,
        ILogger logger)
    {
        // Hardcode your native function registrations here

        var timeSkill = new TimeSkill();
        kernel.ImportSkill(timeSkill, nameof(TimeSkill));

        var chatSkill = new ChatSkill(
            kernel: kernel,
            chatMessageRepository: chatMessageRepository,
            chatSessionRepository: chatSessionRepository,
            promptSettings: promptSettings,
            planner: planner,
            plannerOptions: plannerOptions,
            logger: logger
        );
        kernel.ImportSkill(chatSkill, nameof(ChatSkill));

        var documentMemorySkill = new DocumentMemorySkill(promptSettings, documentMemoryOptions);
        kernel.ImportSkill(documentMemorySkill, nameof(DocumentMemorySkill));
    }
}
