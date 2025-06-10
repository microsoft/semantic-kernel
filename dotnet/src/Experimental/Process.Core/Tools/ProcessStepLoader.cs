// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;

namespace Microsoft.SemanticKernel.Process.Tools;

/// <summary>
/// Helper class to load process steps.
/// </summary>
public static class ProcessStepLoader
{
    /// <summary>
    /// Returns a collection of step types from provided assembly paths.
    /// </summary>
    /// <param name="assemblyPaths">Collection of names or paths of the files that contain the manifest of the assembly.</param>
    public static Dictionary<string, Type> LoadStepTypesFromAssemblies(List<string> assemblyPaths)
    {
        Dictionary<string, Type> stepTypes = [];

        if (assemblyPaths is { Count: > 0 })
        {
            foreach (var assemblyPath in assemblyPaths)
            {
                if (!string.IsNullOrWhiteSpace(assemblyPath))
                {
                    var assembly = Assembly.LoadFrom(assemblyPath);

                    var assemblyStepTypes = assembly.GetTypes()
                        .Where(type => typeof(KernelProcessStep).IsAssignableFrom(type));

                    foreach (var stepType in assemblyStepTypes)
                    {
                        var stepTypeName = stepType.FullName!;
                        var stepAssemblyName = stepType.Assembly.GetName().Name;
                        var stepName = $"{stepType}, {stepAssemblyName}";

                        stepTypes.Add(stepName, stepType);
                    }
                }
            }
        }

        return stepTypes;
    }
}
