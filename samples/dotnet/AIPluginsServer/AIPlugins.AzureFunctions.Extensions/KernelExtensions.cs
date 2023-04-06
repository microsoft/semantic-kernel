// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using Directory = System.IO.Directory;

namespace AIPlugins.AzureFunctions.SKExtensions;

internal static class KernelExtensions
{
    internal static ISKFunction GetFunction(this IReadOnlySkillCollection skills, string skillName, string functionName)
    {
        return skills.HasNativeFunction(skillName, functionName)
            ? skills.GetNativeFunction(skillName, functionName)
            : skills.GetSemanticFunction(skillName, functionName);
    }

    internal static bool HasSemanticOrNativeFunction(this IReadOnlySkillCollection skills, string skillName, string functionName)
    {
        return skills.HasSemanticFunction(skillName, functionName) || skills.HasNativeFunction(skillName, functionName);
    }

    internal static void RegisterPlanner(this IKernel kernel)
    {
        PlannerSkill planner = new(kernel);
        _ = kernel.ImportSkill(planner, nameof(PlannerSkill));
    }

    internal static void RegisterTextMemory(this IKernel kernel)
    {
        _ = kernel.ImportSkill(new TextMemorySkill(), nameof(TextMemorySkill));
    }

    internal static void RegisterSemanticSkills(
        this IKernel kernel,
        string skillsFolder,
        ILogger logger,
        IEnumerable<string>? skillsToLoad = null)
    {
        foreach (string skPromptPath in Directory.EnumerateFiles(skillsFolder, "*.txt", SearchOption.AllDirectories))
        {
            FileInfo fInfo = new(skPromptPath);
            DirectoryInfo? currentFolder = fInfo.Directory;

            while (currentFolder?.Parent?.FullName != skillsFolder)
            {
                currentFolder = currentFolder?.Parent;
            }

            if (ShouldLoad(currentFolder.Name, skillsToLoad))
            {
                try
                {
                    _ = kernel.ImportSemanticSkillFromDirectory(skillsFolder, currentFolder.Name);
                }
                catch (TemplateException e)
                {
                    logger.LogWarning("Could not load skill from {0} with error: {1}", currentFolder.Name, e.Message);
                }
            }
        }
    }

    private static bool ShouldLoad(string skillName, IEnumerable<string>? skillsToLoad = null)
    {
        return skillsToLoad?.Contains(skillName, StringComparer.InvariantCultureIgnoreCase) != false;
    }
}
