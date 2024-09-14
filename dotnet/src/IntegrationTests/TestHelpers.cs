// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Reflection;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.IntegrationTests;

internal static class TestHelpers
{
    private const string PluginsFolder = "../../../../../../prompt_template_samples";

    internal static void ImportAllSamplePlugins(Kernel kernel)
    {
        ImportSamplePromptFunctions(kernel, PluginsFolder,
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

    internal static void ImportAllSampleSkills(Kernel kernel)
    {
        ImportSamplePromptFunctions(kernel, "./skills", "FunSkill");
    }

    internal static IReadOnlyKernelPluginCollection ImportSamplePlugins(Kernel kernel, params string[] pluginNames)
    {
        return ImportSamplePromptFunctions(kernel, PluginsFolder, pluginNames);
    }

    internal static IReadOnlyKernelPluginCollection ImportSamplePromptFunctions(Kernel kernel, string path, params string[] pluginNames)
    {
        string? currentAssemblyDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        if (string.IsNullOrWhiteSpace(currentAssemblyDirectory))
        {
            throw new InvalidOperationException("Unable to determine current assembly directory.");
        }

        string parentDirectory = Path.GetFullPath(Path.Combine(currentAssemblyDirectory, path));

        return new KernelPluginCollection(
            from pluginName in pluginNames
            select kernel.ImportPluginFromPromptDirectory(Path.Combine(parentDirectory, pluginName)));
    }

    internal static void AssertChatErrorExcuseMessage(string content)
    {
        string[] errors = ["error", "difficult", "unable"];

        var matchesAny = errors.Any(e => content.Contains(e, StringComparison.InvariantCultureIgnoreCase));

        Assert.True(matchesAny);
    }
}
