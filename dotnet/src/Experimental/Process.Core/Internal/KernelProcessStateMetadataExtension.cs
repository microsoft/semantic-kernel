// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel.Process.Internal;
internal static class KernelProcessStateMetadataExtension
{
    public static List<KernelProcessStepInfo> BuildWithStateMetadata(this List<ProcessStepBuilder> stepBuilders, KernelProcessStateMetadata? stateMetadata)
    {
        List<KernelProcessStepInfo> builtSteps = [];
        // 1- Validate StateMetadata: Migrate previous state versions if needed + sanitize state
        KernelProcessStateMetadata? sanitizedMetadata = null;
        if (stateMetadata != null)
        {
            sanitizedMetadata = SanitizeProcessStateMetadata(stateMetadata, stepBuilders);
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

    private static KernelProcessStateMetadata SanitizeProcessStateMetadata(KernelProcessStateMetadata stateMetadata, List<ProcessStepBuilder> stepBuilders)
    {
        KernelProcessStateMetadata sanitizedStateMetadata = stateMetadata;
        stepBuilders.ForEach(step =>
        {
            // 1- find matching key name with exact match or by alias match
            string? stepKey = null;

            if (sanitizedStateMetadata.StepsState != null && sanitizedStateMetadata.StepsState.ContainsKey(step.Name))
            {
                stepKey = step.Name;
            }
            else
            {
                stepKey = step.Aliases
                    .Where(alias => sanitizedStateMetadata.StepsState != null && sanitizedStateMetadata.StepsState.ContainsKey(alias))
                    .FirstOrDefault();
            }

            // 2- stepKey match found
            if (stepKey != null)
            {
                var currentVersionStateMetadata = step.BuildStep().ToProcessStateMetadata();
                if (sanitizedStateMetadata.StepsState!.TryGetValue(stepKey, out var savedStateMetadata))
                {
                    if (stepKey != step.Name)
                    {
                        if (savedStateMetadata.VersionInfo == currentVersionStateMetadata.VersionInfo)
                        {
                            // key mismatch only, but same version
                            sanitizedStateMetadata.StepsState[step.Name] = savedStateMetadata;
                            // TODO: Should there be state formatting check too?
                        }
                        else
                        {
                            // version mismatch - check if migration logic in place
                            if (step is ProcessBuilder subprocessBuilder)
                            {
                                var sanitizedStepState = SanitizeProcessStateMetadata((KernelProcessStateMetadata)savedStateMetadata, subprocessBuilder.Steps.ToList());
                                sanitizedStateMetadata.StepsState[step.Name] = sanitizedStepState;
                            }
                            else if (false)
                            {
                                // TODO: Improvements for support on advance versioning scenarios process M:N steps differences https://github.com/microsoft/semantic-kernel/issues/9555
                            }
                            else
                            {
                                // no compatible state found, migrating id only
                                sanitizedStateMetadata.StepsState[step.Name] = new KernelProcessStepStateMetadata()
                                {
                                    Name = step.Name,
                                    Id = step.Id,
                                };
                            }
                        }
                        sanitizedStateMetadata.StepsState[step.Name].Name = step.Name;
                        sanitizedStateMetadata.StepsState.Remove(stepKey);
                    }
                }
            }
        });

        return sanitizedStateMetadata;
    }
}
