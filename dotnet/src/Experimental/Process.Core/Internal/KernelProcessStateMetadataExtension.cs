// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Process.Internal;

internal static class KernelProcessStateMetadataExtension
{
    public static List<KernelProcessStepInfo> BuildWithChildren(this ProcessBuilder processBuilder)
    {
        List<KernelProcessStepInfo> builtSteps = [];

        foreach (ProcessStepBuilder step in processBuilder.Steps)
        {
            builtSteps.Add(step.BuildStep(processBuilder));
        }

        return builtSteps;
    }
}
