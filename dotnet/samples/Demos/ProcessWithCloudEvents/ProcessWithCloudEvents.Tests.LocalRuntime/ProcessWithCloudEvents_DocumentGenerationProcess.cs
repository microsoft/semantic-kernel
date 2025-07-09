// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Processes;
using static ProcessWithCloudEvents.Processes.DocumentGenerationProcess;

namespace ProcessWithCloudEvents.Tests.LocalRuntime;

public class ProcessWithCloudEvents_DocumentGenerationProcess
{
    [Fact]
    public void StartDocumentGenerationOnly()
    {
        var processBuilder = DocumentGenerationProcess.CreateProcessBuilder();

        var t = "";
    }
}
