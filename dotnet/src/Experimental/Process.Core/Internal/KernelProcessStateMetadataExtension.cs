// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel.Process.Internal;
internal static class KernelProcessStateMetadataExtension
{
    public static List<KernelProcessStepInfo> BuildWithStateMetadata(this List<ProcessStepBuilder> stepBuilders, KernelProcessStateMetadata? stateMetadata)
    {
        List<KernelProcessStepInfo> builtSteps = [];
        // 1- Validate StateMetadata: Migrate previous state versions if needed + check state is valid
        KernelProcessStateMetadata? sanitizedMetadata = stateMetadata;
        if (stateMetadata != null)
        {
            // TODO: placeholder for adding state sanitization
        }

        // 2- Build steps info with validated stateMetadata
        stepBuilders.ForEach(step =>
        {
            if (sanitizedMetadata != null && sanitizedMetadata.StepsState != null && sanitizedMetadata.StepsState.TryGetValue(step.Name, out var stepStateObject) && stepStateObject != null)
            {
                builtSteps.Add(step.BuildStep(stepStateObject));
                return;
            }

            builtSteps.Add(step.BuildStep());
        });

        return builtSteps;
    }
}
