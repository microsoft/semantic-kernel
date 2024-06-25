// Copyright (c) Microsoft. All rights reserved.


using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TemplateEngine;

namespace AIPlugins.AzureFunctions.Extensions;
public static class KernelExtensions
{
    public static void RegisterSemanticSkills(
      this IKernel kernel,
      string skillsFolder,
      ILogger logger,
      IEnumerable<string>? skillsToLoad = null)
    {
        foreach (string skPromptPath in Directory.EnumerateFiles(skillsFolder, "*.txt", SearchOption.AllDirectories))
        {
            FileInfo fInfo = new(skPromptPath);
            DirectoryInfo? currentFolder = fInfo.Directory;

            while (currentFolder?.Parent?.Name != skillsFolder)
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
