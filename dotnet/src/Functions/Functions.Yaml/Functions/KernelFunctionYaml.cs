// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Models;
using Microsoft.SemanticKernel.TemplateEngine;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel.Functions.Yaml.Functions;
/// <summary>
/// Factory methods for creating <seealso cref="ISKFunction"/> instances.
/// </summary>
public static class KernelFunctionYaml
{
    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a semantic function using the specified markdown text.
    /// </summary>
    /// <param name="resourceName">Resource containing the YAML representation of the <see cref="PromptModel"/> to use to create the semantic function</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="ISKFunction"/>.</returns>
    public static ISKFunction CreateFromPromptYamlResource(
        string resourceName,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        var assembly = Assembly.GetExecutingAssembly();
        string resourcePath = resourceName;

        using Stream stream = assembly.GetManifestResourceStream(resourcePath);
        using StreamReader reader = new(stream);
        var text = reader.ReadToEnd();

        return CreateFromPromptYaml(
            text,
            pluginName,
            promptTemplateFactory,
            loggerFactory);
    }

    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a semantic function using the specified markdown text.
    /// </summary>
    /// <param name="text">YAML representation of the <see cref="PromptModel"/> to use to create the semantic function</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="ISKFunction"/>.</returns>
    public static ISKFunction CreateFromPromptYaml(
        string text,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithNodeDeserializer(new AIRequestSettingsNodeDeserializer())
            .Build();

        var semanticFunctionConfig = deserializer.Deserialize<PromptModel>(text);

        return SKFunction.Create(
            semanticFunctionConfig,
            pluginName,
            promptTemplateFactory,
            loggerFactory);
    }
}
