// Copyright (c) Microsoft. All rights reserved.
using System;
using OpenAI.Assistants;
using OpenAI.Responses;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Extensions for <see cref="KernelFunction"/> to support OpenAI specific operations.
/// </summary>
public static class KernelFunctionExtensions
{
    /// <summary>
    /// Convert <see cref="KernelFunction"/> to an OpenAI tool model.
    /// </summary>
    /// <param name="function">The source function</param>
    /// <param name="pluginName">The plugin name</param>
    /// <returns>An OpenAI tool definition</returns>
    public static FunctionToolDefinition ToToolDefinition(this KernelFunction function, string? pluginName = null)
    {
        if (function.Metadata.Parameters.Count > 0)
        {
            BinaryData parameterData = function.Metadata.CreateParameterSpec();

            return new FunctionToolDefinition(FunctionName.ToFullyQualifiedName(function.Name, pluginName ?? function.PluginName))
            {
                Description = function.Description,
                Parameters = parameterData,
            };
        }

        return new FunctionToolDefinition(FunctionName.ToFullyQualifiedName(function.Name, pluginName ?? function.PluginName))
        {
            Description = function.Description
        };
    }

    /// <summary>
    /// Converts a <see cref="KernelFunction"/> into a <see cref="ResponseTool"/> representation.
    /// </summary>
    /// <remarks>If the <paramref name="function"/> has parameters, they are included in the resulting <see
    /// cref="ResponseTool"/>  as a serialized parameter specification. Otherwise, the parameters are set to <see
    /// langword="null"/>.</remarks>
    /// <param name="function">The <see cref="KernelFunction"/> to convert.</param>
    /// <param name="pluginName">An optional plugin name to associate with the function. If not provided, the function's default plugin name is
    /// used.</param>
    /// <param name="functionSchemaIsStrict">A value indicating whether the function's schema should be treated as strict.  If <see langword="true"/>, the
    /// schema will enforce stricter validation rules.</param>
    /// <returns>A <see cref="ResponseTool"/> that represents the specified <see cref="KernelFunction"/>.</returns>
    public static ResponseTool ToResponseTool(this KernelFunction function, string? pluginName = null, bool functionSchemaIsStrict = false)
    {
        if (function.Metadata.Parameters.Count > 0)
        {
            BinaryData parameterData = function.Metadata.CreateParameterSpec();
            return ResponseTool.CreateFunctionTool(
                functionName: FunctionName.ToFullyQualifiedName(function.Name, pluginName ?? function.PluginName),
                functionParameters: parameterData,
                strictModeEnabled: functionSchemaIsStrict,
                functionDescription: function.Description);
        }

        return ResponseTool.CreateFunctionTool(
            functionName: FunctionName.ToFullyQualifiedName(function.Name, pluginName ?? function.PluginName),
            functionParameters: s_emptyFunctionParameters,
            null,
            functionDescription: function.Description);
    }

    #region private
    private static readonly BinaryData s_emptyFunctionParameters = BinaryData.FromString("{}");
    #endregion
}
