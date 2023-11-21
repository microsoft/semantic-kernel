// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;

namespace SemanticKernel.UnitTests;

/// <summary>
/// Mock implementation of <see cref="KernelFunction"/> for unit testing.
/// </summary>
public class KernelFunctionMock : KernelFunction
{
    public Func<SKFunctionMetadata>? GetMetadataDelegate { get; set; }
    public Func<Kernel, SKContext, AIRequestSettings?, CancellationToken, Task<FunctionResult>>? InvokeCoreDelegate { get; set; }

    public KernelFunctionMock(string? name = null, string? description = null, IEnumerable<AIRequestSettings>? modelSettings = null) : base(name ?? string.Empty, description ?? string.Empty, modelSettings)
    {
    }

    protected override Task<FunctionResult> InvokeCoreAsync(Kernel kernel, SKContext context, AIRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        if (this.InvokeCoreDelegate is null)
        {
            return Task.FromResult(new FunctionResult(this.Name, context));
        }

        return this.InvokeCoreDelegate(kernel, context, requestSettings, cancellationToken);
    }

    public override SKFunctionMetadata GetMetadata()
    {
        if (this.GetMetadataDelegate is null)
        {
            return new SKFunctionMetadata(this.Name);
        }

        return this.GetMetadataDelegate();
    }
}
