// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ProcessWithCloudEvents.Processes.Steps;

public class CounterInterceptorStep : KernelProcessStep
{
    public static class Functions
    {
        public const string InterceptCounter = nameof(InterceptCounter);
    }

    [KernelFunction(Functions.InterceptCounter)]
    public int? InterceptCounter(int counterStatus)
    {
        var multipleOf = 3;
        if (counterStatus != 0 && counterStatus % multipleOf == 0)
        {
            // Only return counter if counter is a multiple of "multipleOf"
            return counterStatus;
        }

        return null;
    }
}
