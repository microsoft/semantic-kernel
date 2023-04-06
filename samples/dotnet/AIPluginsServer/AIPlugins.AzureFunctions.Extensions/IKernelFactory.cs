// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace AIPlugins.AzureFunctions.SKExtensions;

public interface IKernelFactory
{
    public IKernel CreateKernel();
}
