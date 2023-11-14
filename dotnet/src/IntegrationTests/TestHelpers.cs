// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Reflection;
using Microsoft.SemanticKernel;

namespace SemanticKernel.IntegrationTests;

internal static class TestHelpers
{
    internal static void ImportAllSamplePlugins(IKernel kernel)
    {
        ImportSampleSemanticFunctions(kernel, "../../../../../../samples/plugins",
            "ChatPlugin",
            "SummarizePlugin",
            "WriterPlugin",
            "CalendarPlugin",
            "ChildrensBookPlugin",
            "ClassificationPlugin",
            "CodingPlugin",
            "FunPlugin",
            "IntentDetectionPlugin",
            "MiscPlugin",
            "QAPlugin");
    }

    internal static void ImportAllSampleSkills(IKernel kernel)
    {
        ImportSampleSemanticFunctions(kernel, "../../../../../../samples/skills",
            "ChatSkill",
            "SummarizeSkill",
            "WriterSkill",
            "CalendarSkill",
            "ChildrensBookSkill",
            "ClassificationSkill",
            "CodingSkill",
            "FunSkill",
            "IntentDetectionSkill",
            "MiscSkill",
            "QASkill");
    }

    internal static ISKPluginCollection ImportSamplePlugins(IKernel kernel, params string[] pluginNames)
    {
        return ImportSampleSemanticFunctions(kernel, "../../../../../../samples/plugins", pluginNames);
    }

    internal static ISKPluginCollection ImportSampleSemanticFunctions(IKernel kernel, string path, params string[] pluginNames)
    {
        string? currentAssemblyDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        if (string.IsNullOrWhiteSpace(currentAssemblyDirectory))
        {
            throw new InvalidOperationException("Unable to determine current assembly directory.");
        }

        string parentDirectory = Path.GetFullPath(Path.Combine(currentAssemblyDirectory, path));

        return new SKPluginCollection(
            from pluginName in pluginNames
            select kernel.ImportPluginFromPromptDirectory(Path.Combine(parentDirectory, pluginName)));
    }
}
