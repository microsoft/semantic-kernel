// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace AIPlugins.AzureFunctions.Extensions;

public interface IKernelFactory
{
    public IKernel CreateKernel();
}
