// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>Provides a <see cref="KernelFunction"/> that wraps an <see cref="AIFunction"/>.</summary>
/// <remarks>
/// The implementation should largely be unused, other than for its <see cref="AIFunction.Metadata"/>. The implementation of
/// <see cref="ChatCompletionServiceChatClient"/> only manufactures these to pass along to the underlying
/// <see cref="IChatCompletionService"/> with autoInvoke:false, which means the <see cref="IChatCompletionService"/>
/// implementation shouldn't be invoking these functions at all. As such, the <see cref="InvokeCoreAsync"/> and
/// <see cref="InvokeStreamingCoreAsync"/> methods both unconditionally throw, even though they could be implemented.
/// </remarks>
internal sealed class AIFunctionKernelFunction : KernelFunction
{
    private readonly AIFunction _aiFunction;

    public AIFunctionKernelFunction(AIFunction aiFunction) :
        base(aiFunction.Metadata.Name,
            aiFunction.Metadata.Description,
            aiFunction.Metadata.Parameters.Select(p => new KernelParameterMetadata(p.Name, AbstractionsJsonContext.Default.Options)
            {
                Description = p.Description,
                DefaultValue = p.DefaultValue,
                IsRequired = p.IsRequired,
                ParameterType = p.ParameterType,
                Schema =
                    p.Schema is JsonElement je ? new KernelJsonSchema(je) :
                    p.Schema is string s ? new KernelJsonSchema(JsonSerializer.Deserialize(s, AbstractionsJsonContext.Default.JsonElement)) :
                    null,
            }).ToList(),
            AbstractionsJsonContext.Default.Options,
            new KernelReturnParameterMetadata(AbstractionsJsonContext.Default.Options)
            {
                Description = aiFunction.Metadata.ReturnParameter.Description,
                ParameterType = aiFunction.Metadata.ReturnParameter.ParameterType,
                Schema =
                    aiFunction.Metadata.ReturnParameter.Schema is JsonElement je ? new KernelJsonSchema(je) :
                    aiFunction.Metadata.ReturnParameter.Schema is string s ? new KernelJsonSchema(JsonSerializer.Deserialize(s, AbstractionsJsonContext.Default.JsonElement)) :
                    null,
            })
    {
        this._aiFunction = aiFunction;
    }

    private AIFunctionKernelFunction(AIFunctionKernelFunction other, string pluginName) :
        base(other.Name, pluginName, other.Description, other.Metadata.Parameters, AbstractionsJsonContext.Default.Options, other.Metadata.ReturnParameter)
    {
        this._aiFunction = other._aiFunction;
    }

    public override KernelFunction Clone(string pluginName)
    {
        Verify.NotNullOrWhiteSpace(pluginName);
        return new AIFunctionKernelFunction(this, pluginName);
    }

    protected override ValueTask<FunctionResult> InvokeCoreAsync(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        // This should never be invoked, as instances are always passed with autoInvoke:false.
        throw new NotSupportedException();
    }

    protected override IAsyncEnumerable<TResult> InvokeStreamingCoreAsync<TResult>(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        // This should never be invoked, as instances are always passed with autoInvoke:false.
        throw new NotSupportedException();
    }
}
