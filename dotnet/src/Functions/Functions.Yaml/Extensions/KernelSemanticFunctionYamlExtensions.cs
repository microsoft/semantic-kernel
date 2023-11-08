// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;
using Microsoft.SemanticKernel.Functions.Yaml.Models;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the namespace of IKernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods to define semantic functions using YAML format.
/// </summary>
public static class KernelSemanticFunctionYamlExtensions
{
    /// <summary>
    /// 
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="resourceName"></param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateSemanticFunctionFromYamlResource(
        this IKernel kernel,
        string resourceName)
    {
        // Determine path
        var assembly = Assembly.GetExecutingAssembly();
        string resourcePath = resourceName;
        // Format: "{Namespace}.{Folder}.{filename}.{Extension}"
        /*
        if (!name.StartsWith(nameof(SignificantDrawerCompiler)))
        {
            resourcePath = assembly.GetManifestResourceNames()
                .Single(str => str.EndsWith(name));
        }
        */

        using Stream stream = assembly.GetManifestResourceStream(resourcePath);
        using StreamReader reader = new(stream);
        var text = reader.ReadToEnd();

        return kernel.CreateSemanticFunctionFromYaml(text);
    }

    /// <summary>
    /// 
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="text"></param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateSemanticFunctionFromYaml(
        this IKernel kernel,
        string text)
    {
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .Build();

        var semanticFunctionModel = deserializer.Deserialize<SemanticFunctionModel>(text);

        var functionName = semanticFunctionModel.Name;
        var pluginName = semanticFunctionModel.PluginName;
        var promptTemplate = semanticFunctionModel.Template;
        var promptTemplateConfig = semanticFunctionModel.GetPromptTemplateConfig();

        return kernel.CreateSemanticFunction(
           promptTemplate: promptTemplate,
           promptTemplateConfig: promptTemplateConfig,
           functionName: functionName,
           pluginName: pluginName);
    }
}
