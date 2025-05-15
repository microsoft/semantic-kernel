// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Process.Internal;

internal static class KernelProcessStepEdgesExtensions
{
    public static Dictionary<string, Dictionary<string, KernelProcessEventData?>> PackStepEdgesValues(this Dictionary<string, Dictionary<string, object?>?> functionsParameters)
    {
        Dictionary<string, Dictionary<string, KernelProcessEventData?>> stepFunctionParamsEventData = [];
        foreach (var function in functionsParameters)
        {
            var functionName = function.Key;
            stepFunctionParamsEventData[functionName] = [];
            foreach (var parameterData in function.Value ?? [])
            {
                var parameterName = parameterData.Key;
                if (parameterData.Value is null)
                {
                    stepFunctionParamsEventData[functionName][parameterName] = null;
                    continue;
                }

                // Avoid storing parameters that are automatically injected by the step
                // Must match cases in StepExtensions.FindInputChannels
                if (parameterData.Value is Kernel or KernelProcessStepContext or KernelProcessStepExternalContext)
                {
                    continue;
                }

                stepFunctionParamsEventData[functionName][parameterName] = KernelProcessEventData.FromObject(parameterData.Value);
            }
        }

        return stepFunctionParamsEventData;
    }
}
