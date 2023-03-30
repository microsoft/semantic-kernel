// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.TemplateEngine;

namespace SemanticKernel.Service;

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

    internal static Dictionary<string, Type> RegisterNativeSkillDependencies(
        this IServiceCollection serviceProvider,
        string skillDirectory)
    {
        // TODO: Implement this method

        return new Dictionary<string, Type>();
    }

    internal static void RegisterNativeSkills(
        this IKernel kernel,
        IServiceProvider serviceProvider,
        IDictionary<string, Type> skillsToRegister,
        ILogger logger)
    {
        foreach (KeyValuePair<string, Type> skill in skillsToRegister)
        {
            var skillInstance = serviceProvider.GetService(skill.Value);

            if (skillInstance != null)
            {
                kernel.ImportSkill(skillInstance, skill.Key);
            }
            else
            {
                logger.LogError("Failed to get an instance of {SkillName} from DI container", skill.Key);
            }
        }
    }
}
