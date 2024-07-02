// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using OpenAI.Chat;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Represents a function parameter that can be passed to an AzureOpenAI function tool call.
/// </summary>
public sealed class AzureOpenAIFunctionParameter
{
    internal AzureOpenAIFunctionParameter(string? name, string? description, bool isRequired, Type? parameterType, KernelJsonSchema? schema)
    {
        this.Name = name ?? string.Empty;
        this.Description = description ?? string.Empty;
        this.IsRequired = isRequired;
        this.ParameterType = parameterType;
        this.Schema = schema;
    }

    /// <summary>Gets the name of the parameter.</summary>
    public string Name { get; }

    /// <summary>Gets a description of the parameter.</summary>
    public string Description { get; }

    /// <summary>Gets whether the parameter is required vs optional.</summary>
    public bool IsRequired { get; }

    /// <summary>Gets the <see cref="Type"/> of the parameter, if known.</summary>
    public Type? ParameterType { get; }

    /// <summary>Gets a JSON schema for the parameter, if known.</summary>
    public KernelJsonSchema? Schema { get; }
}

/// <summary>
/// Represents a function return parameter that can be returned by a tool call to AzureOpenAI.
/// </summary>
public sealed class AzureOpenAIFunctionReturnParameter
{
    internal AzureOpenAIFunctionReturnParameter(string? description, Type? parameterType, KernelJsonSchema? schema)
    {
        this.Description = description ?? string.Empty;
        this.Schema = schema;
        this.ParameterType = parameterType;
    }

    /// <summary>Gets a description of the return parameter.</summary>
    public string Description { get; }

    /// <summary>Gets the <see cref="Type"/> of the return parameter, if known.</summary>
    public Type? ParameterType { get; }

    /// <summary>Gets a JSON schema for the return parameter, if known.</summary>
    public KernelJsonSchema? Schema { get; }
}

/// <summary>
/// Represents a function that can be passed to the AzureOpenAI API
/// </summary>
public sealed class AzureOpenAIFunction
{
    /// <summary>
    /// Cached <see cref="BinaryData"/> storing the JSON for a function with no parameters.
    /// </summary>
    /// <remarks>
    /// This is an optimization to avoid serializing the same JSON Schema over and over again
    /// for this relatively common case.
    /// </remarks>
    private static readonly BinaryData s_zeroFunctionParametersSchema = new("""{"type":"object","required":[],"properties":{}}""");
    /// <summary>
    /// Cached schema for a descriptionless string.
    /// </summary>
    private static readonly KernelJsonSchema s_stringNoDescriptionSchema = KernelJsonSchema.Parse("""{"type":"string"}""");

    /// <summary>Initializes the OpenAIFunction.</summary>
    internal AzureOpenAIFunction(
        string? pluginName,
        string functionName,
        string? description,
        IReadOnlyList<AzureOpenAIFunctionParameter>? parameters,
        AzureOpenAIFunctionReturnParameter? returnParameter)
    {
        Verify.NotNullOrWhiteSpace(functionName);

        this.PluginName = pluginName;
        this.FunctionName = functionName;
        this.Description = description;
        this.Parameters = parameters;
        this.ReturnParameter = returnParameter;
    }

    /// <summary>Gets the separator used between the plugin name and the function name, if a plugin name is present.</summary>
    /// <remarks>This separator was previously <c>_</c>, but has been changed to <c>-</c> to better align to the behavior elsewhere in SK and in response
    /// to developers who want to use underscores in their function or plugin names. We plan to make this setting configurable in the future.</remarks>
    public static string NameSeparator { get; set; } = "-";

    /// <summary>Gets the name of the plugin with which the function is associated, if any.</summary>
    public string? PluginName { get; }

    /// <summary>Gets the name of the function.</summary>
    public string FunctionName { get; }

    /// <summary>Gets the fully-qualified name of the function.</summary>
    /// <remarks>
    /// This is the concatenation of the <see cref="PluginName"/> and the <see cref="FunctionName"/>,
    /// separated by <see cref="NameSeparator"/>. If there is no <see cref="PluginName"/>, this is
    /// the same as <see cref="FunctionName"/>.
    /// </remarks>
    public string FullyQualifiedName =>
        string.IsNullOrEmpty(this.PluginName) ? this.FunctionName : $"{this.PluginName}{NameSeparator}{this.FunctionName}";

    /// <summary>Gets a description of the function.</summary>
    public string? Description { get; }

    /// <summary>Gets a list of parameters to the function, if any.</summary>
    public IReadOnlyList<AzureOpenAIFunctionParameter>? Parameters { get; }

    /// <summary>Gets the return parameter of the function, if any.</summary>
    public AzureOpenAIFunctionReturnParameter? ReturnParameter { get; }

    /// <summary>
    /// Converts the <see cref="AzureOpenAIFunction"/> representation to the Azure SDK's
    /// <see cref="ChatTool"/> representation.
    /// </summary>
    /// <returns>A <see cref="ChatTool"/> containing all the function information.</returns>
    public ChatTool ToFunctionDefinition()
    {
        BinaryData resultParameters = s_zeroFunctionParametersSchema;

        IReadOnlyList<AzureOpenAIFunctionParameter>? parameters = this.Parameters;
        if (parameters is { Count: > 0 })
        {
            var properties = new Dictionary<string, KernelJsonSchema>();
            var required = new List<string>();

            for (int i = 0; i < parameters.Count; i++)
            {
                var parameter = parameters[i];
                properties.Add(parameter.Name, parameter.Schema ?? GetDefaultSchemaForTypelessParameter(parameter.Description));
                if (parameter.IsRequired)
                {
                    required.Add(parameter.Name);
                }
            }

            resultParameters = BinaryData.FromObjectAsJson(new
            {
                type = "object",
                required,
                properties,
            });
        }

        return ChatTool.CreateFunctionTool
        (
            functionName: this.FullyQualifiedName,
            functionDescription: this.Description,
            functionParameters: resultParameters
        );
    }

    /// <summary>Gets a <see cref="KernelJsonSchema"/> for a typeless parameter with the specified description, defaulting to typeof(string)</summary>
    private static KernelJsonSchema GetDefaultSchemaForTypelessParameter(string? description)
    {
        // If there's a description, incorporate it.
        if (!string.IsNullOrWhiteSpace(description))
        {
            return KernelJsonSchemaBuilder.Build(null, typeof(string), description);
        }

        // Otherwise, we can use a cached schema for a string with no description.
        return s_stringNoDescriptionSchema;
    }
}
