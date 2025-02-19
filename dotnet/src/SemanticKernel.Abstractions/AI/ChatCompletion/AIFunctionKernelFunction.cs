// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>Provides a <see cref="KernelFunction"/> that wraps an <see cref="AIFunction"/>.</summary>
/// <remarks>
/// The implementation of <see cref="ChatCompletionServiceChatClient"/> only manufactures these to pass along to the underlying
/// <see cref="IChatCompletionService"/> with autoInvoke:false, which means the <see cref="IChatCompletionService"/>
/// implementation shouldn't be invoking these functions at all. As such, the <see cref="InvokeCoreAsync"/> and
/// <see cref="InvokeStreamingCoreAsync"/> methods both unconditionally throw, even though they could be implemented.
/// </remarks>
internal sealed class AIFunctionKernelFunction : KernelFunction
{
    private readonly AIFunction _aiFunction;

    public AIFunctionKernelFunction(AIFunction aiFunction) :
        base(aiFunction.Name,
            aiFunction.Description,
            MapParameterMetadata(aiFunction),
            aiFunction.JsonSerializerOptions,
            new KernelReturnParameterMetadata(AbstractionsJsonContext.Default.Options)
            {
                Description = aiFunction.UnderlyingMethod?.ReturnParameter.GetCustomAttribute<DescriptionAttribute>()?.Description,
                ParameterType = aiFunction.UnderlyingMethod?.ReturnParameter.ParameterType,
                Schema = new KernelJsonSchema(AIJsonUtilities.CreateJsonSchema(aiFunction.UnderlyingMethod?.ReturnParameter.ParameterType)),
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

    private static IReadOnlyList<KernelParameterMetadata> MapParameterMetadata(AIFunction aiFunction)
    {
        if (!aiFunction.JsonSchema.TryGetProperty("properties", out JsonElement properties))
        {
            return Array.Empty<KernelParameterMetadata>();
        }

        List<KernelParameterMetadata> kernelParams = [];
        var parameterInfos = aiFunction.UnderlyingMethod?.GetParameters().ToDictionary(p => p.Name!, StringComparer.Ordinal);
        foreach (var param in properties.EnumerateObject())
        {
            ParameterInfo? paramInfo = null;
            parameterInfos?.TryGetValue(param.Name, out paramInfo);
            kernelParams.Add(new(param.Name, aiFunction.JsonSerializerOptions)
            {
                Description = param.Value.TryGetProperty("description", out JsonElement description) ? description.GetString() : null,
                DefaultValue = param.Value.TryGetProperty("default", out JsonElement defaultValue) ? defaultValue : null,
                IsRequired = param.Value.TryGetProperty("required", out JsonElement required) && required.GetBoolean(),
                ParameterType = paramInfo?.ParameterType,
                Schema = param.Value.TryGetProperty("schema", out JsonElement schema) ? new KernelJsonSchema(schema) : null,
            });
        }

        return kernelParams;
    }
}
