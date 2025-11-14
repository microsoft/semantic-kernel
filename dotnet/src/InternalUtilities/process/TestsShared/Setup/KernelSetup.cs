// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable IDE0005 // Using directive is unnecessary
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Process.TestsShared.Services;
#pragma warning restore IDE0005 // Using directive is unnecessary

namespace Microsoft.SemanticKernel.Process.TestsShared.Setup;

internal static class KernelSetup
{
    public static Kernel SetupKernelWithCounterService(CounterService counterService)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<ICounterService>(counterService);

        return builder.Build();
    }
}
