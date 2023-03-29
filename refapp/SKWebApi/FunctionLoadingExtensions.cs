// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.TemplateEngine;

namespace SemanticKernel.Service;

internal static class FunctionLoadingExtensions
{
    internal static void RegisterSemanticSkills(
        this IKernel kernel,
        string skillDirectory,
        ILogger logger)
    {
        string fullPath = Path.GetFullPath(skillDirectory).TrimEnd(Path.DirectorySeparatorChar);
        string skillName = Path.GetFileName(fullPath);

        try
        {
            kernel.ImportSemanticSkillFromDirectory(skillDirectory.Substring(0, skillDirectory.Length - skillName.Length), skillName);
        }
        catch (TemplateException e)
        {
            logger.LogWarning("Could not load skill from {Directory}: {Message}", skillDirectory, e.Message);
        }
    }

    internal static void RegisterSemanticSkill(
        this IKernel kernel,
        string skillDirectory,
        ILogger logger)
    {
        string fullPath = Path.GetFullPath(skillDirectory).TrimEnd(Path.DirectorySeparatorChar);
        string skillName = Path.GetFileName(fullPath);

        try
        {
            kernel.ImportSemanticSkillFromDirectory(skillDirectory.Substring(0, skillDirectory.Length - skillName.Length), skillName);
        }
        catch (TemplateException e)
        {
            logger.LogWarning("Could not load skill from {Directory}: {Message}", skillDirectory, e.Message);
        }
    }

    /*internal static void RegisterNativeSkillDependencies(
        this IKernel kernel,
        string skillDirectory,
        ILogger logger)
    {
        // object skill = new ();
        // kernel.ImportSkill(skill, nameof(DocumentSkill));

        Assembly.Load("xxx")
            .GetTypes()
            .Where(w => w.Namespace == "xxx.Repository" && w.IsClass)
            .ToList()
            .ForEach(t => {
                services.AddTransient(t.GetInterface("I" + t.Name, false), t);
            });

        // load assembly and register with DI  
        var assembly = Assembly.LoadFrom(Path.Combine("..\\Controllers\\bin\\Debug\\netcoreapp3.1", "Orders.dll"));
        var orderType = assembly.ExportedTypes.First(t => t.Name == "Order");
        services.AddScoped(orderType); // this is where we would make our type known to the DI container  
        var loadedTypesCache = new LoadedTypesCache(); // this step is optional - i chose to leverage the same DI mechanism to avoid having to load assembly in my controller for type definition.  
        loadedTypesCache.LoadedTypes.Add("order", orderType);
        services.AddSingleton(loadedTypesCache); // singleton seems like a good fit here 
    }*/

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
