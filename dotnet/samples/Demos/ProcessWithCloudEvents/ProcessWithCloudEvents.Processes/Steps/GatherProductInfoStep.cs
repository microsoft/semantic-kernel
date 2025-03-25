// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ProcessWithCloudEvents.Processes.Steps;

public class GatherProductInfoStep : KernelProcessStep
{
    [KernelFunction]
    public string OnReceiveUserRequest(string productInfo)
    {
        Console.WriteLine(productInfo);
        return productInfo;
    }
}
