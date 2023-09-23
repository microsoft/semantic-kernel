// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using Microsoft.SemanticKernel;

namespace SemanticKernel.IntegrationTests;

internal static class TestHelpers
{
    internal static void ImportAllSamplePlugins(IKernel kernel)
    {
        var chatPlugin = ImportSamplePlugins(kernel,
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

    internal static IDictionary<string, ISKFunction> ImportSamplePlugins(IKernel kernel, params string[] pluginNames)
    {
        string? currentAssemblyDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        if (string.IsNullOrWhiteSpace(currentAssemblyDirectory))
        {
            throw new InvalidOperationException("Unable to determine current assembly directory.");
        }

        string parentDirectory = Path.GetFullPath(Path.Combine(currentAssemblyDirectory, "../../../../../../samples/plugins"));

        return kernel.ImportSemanticFunctionsFromDirectory(parentDirectory, pluginNames);
    }
}
