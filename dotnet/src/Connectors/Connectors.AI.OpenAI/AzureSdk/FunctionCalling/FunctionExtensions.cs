// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk.FunctionCalling;

using System;
using System.Collections.Generic;
using System.Linq;
using Azure.AI.OpenAI;
using SkillDefinition;


/// <summary>
///  Extensions for converting between FunctionDefinition and FunctionView
/// </summary>
public static class FunctionExtensions
{
    /// <summary>
    ///  Convert FunctionView to FunctionDefinition
    /// </summary>
    /// <param name="functionView"></param>
    /// <returns></returns>
    public static FunctionDefinition ToFunctionDefinition(this FunctionView functionView)
    {
        // Convert Parameters 
        var paramObjects = functionView.Parameters.Select(param => new
        {
            name = param.Name,
            description = param.Description,
            defaultValue = param.DefaultValue,
            type = param.Type?.ToString()
        }).ToArray();

        // Form parameters as BinaryData
        var parameters = BinaryData.FromObjectAsJson(new
        {
            type = "object",
            properties = paramObjects,
            required = paramObjects.Select(p => p.name)
        });

        // Create FunctionDefinition
        return new FunctionDefinition()
        {
            Name = functionView.Name,
            Description = functionView.Description,
            Parameters = parameters
        };
    }


    /// <summary>
    ///  Convert FunctionDefinition to FunctionView
    /// </summary>
    /// <param name="functionDefinition"></param>
    /// <returns></returns>
    public static FunctionView ToFunctionView(this FunctionDefinition functionDefinition)
    {
        // Convert Parameters 
        ParameterView[] parameters = functionDefinition.Parameters.ToObjectFromJson<ParameterView[]>();

        // Create FunctionView
        return new FunctionView()
        {
            Name = functionDefinition.Name,
            Description = functionDefinition.Description,
            Parameters = parameters
        };
    }


    /// <summary>
    ///  Convert FunctionsView to FunctionDefinitions
    /// </summary>
    /// <param name="functionsView"></param>
    /// <returns></returns>
    public static IEnumerable<FunctionDefinition> ToFunctionDefinitions(this FunctionsView functionsView)
    {
        List<FunctionView> functionViews = functionsView.NativeFunctions.SelectMany(function => function.Value).ToList();
        functionViews.AddRange(functionsView.SemanticFunctions.SelectMany(function => function.Value));

        return functionViews.Select(functionView => functionView.ToFunctionDefinition());
    }
}
