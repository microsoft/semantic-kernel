// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ProductDocumentation.Steps;

public sealed class PublishDocumentationStep : KernelProcessStep
{
    [KernelFunction]
    public string PublishDocumentation()
    {
        return "Publishing product documentation...";
    }
}
