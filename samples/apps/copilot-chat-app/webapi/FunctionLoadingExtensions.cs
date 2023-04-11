// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.TemplateEngine;
using SemanticKernel.Service.Skills;
using SKWebApi.Skills;
using SKWebApi.Storage;

namespace CopilotChatApi.Service;

internal static class FunctionLoadingExtensions
{
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

    internal static void RegisterNativeSkills(
        this IKernel kernel,
        InMemoryContext<Chat> chatMemoryContext,
        InMemoryContext<ChatMessage> chatMessageMemoryContext,
        ILogger logger)
    {
        // Hardcode your native function registrations here

        var timeSkill = new TimeSkill();
        kernel.ImportSkill(timeSkill, nameof(TimeSkill));

        var chatSkill = new ChatSkill(
            kernel,
            new ChatMessageRepository(chatMessageMemoryContext),
            new ChatRepository(chatMemoryContext)
        );
        kernel.ImportSkill(chatSkill, nameof(ChatSkill));

        var chatMemorySkill = new ChatMemorySkill(
            new ChatMessageRepository(chatMessageMemoryContext),
            new ChatRepository(chatMemoryContext)
        );
        kernel.ImportSkill(chatMemorySkill, nameof(ChatMemorySkill));
    }
}
