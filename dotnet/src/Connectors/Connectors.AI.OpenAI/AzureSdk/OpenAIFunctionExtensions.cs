// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Extensions for <see cref="FunctionView"/> specific to the OpenAI connector.
/// </summary>
internal static class OpenAIFunctionExtensions
{
    /// <summary>
    /// Convert a <see cref="OpenAIFunction"/> to an <see cref="FunctionView"/>.
    /// </summary>
    /// <param name="function">The <see cref="OpenAIFunction"/> object to convert.</param>
    /// <returns>An <see cref="FunctionView"/> object.</returns>
    public static FunctionView ToFunctionView(this OpenAIFunction function)
    {
        var parameterViews = new List<ParameterView>();
        foreach (var openAIparameter in function.Parameters)
        {
            parameterViews.Add(new ParameterView(
                Name: openAIparameter.Name,
                Description: openAIparameter.Description,
                IsRequired: openAIparameter.IsRequired,
                Schema: openAIparameter.Schema,
                ParameterType: openAIparameter.ParameterType));
        }

        var returnParameter = new ReturnParameterView(
            Description: function.ReturnParameter.Description,
            Schema: function.ReturnParameter.Schema,
            ParameterType: function.ReturnParameter.ParameterType);

        return new FunctionView(
            Name: function.FunctionName,
            PluginName: function.PluginName,
            Description: function.Description,
            Parameters: parameterViews,
            ReturnParameter: returnParameter);
    }
}
