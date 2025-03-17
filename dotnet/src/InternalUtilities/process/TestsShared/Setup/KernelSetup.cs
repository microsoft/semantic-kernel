// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using SemanticKernel.Process.TestsShared.Services;

namespace SemanticKernel.Process.TestsShared.Setup;

internal static class KernelSetup
{
    public static Kernel SetupKernelWithCounterService(CounterService counterService)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<ICounterService>(counterService);

        return builder.Build();
    }
}
