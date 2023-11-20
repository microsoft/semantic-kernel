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
/// Factory methods for creating <seealso cref="SKFunction"/> instances.
/// </summary>
public static class SKFunctionYaml
{
    /// <summary>
    /// Creates an <see cref="SKFunction"/> instance for a semantic function using the specified markdown text.
    /// </summary>
    /// <param name="resourceName">Resource containing the YAML representation of the <see cref="PromptFunctionModel"/> to use to create the semantic function</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="SKFunction"/>.</returns>
    public static SKFunction FromPromptYamlResource(
        string resourceName,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        var assembly = Assembly.GetExecutingAssembly();
        string resourcePath = resourceName;

        using Stream stream = assembly.GetManifestResourceStream(resourcePath);
        using StreamReader reader = new(stream);
        var text = reader.ReadToEnd();

        return FromPromptYaml(
            text,
            promptTemplateFactory,
            loggerFactory);
    }

    /// <summary>
    /// Creates an <see cref="SKFunction"/> instance for a semantic function using the specified markdown text.
    /// </summary>
    /// <param name="text">YAML representation of the <see cref="PromptFunctionModel"/> to use to create the semantic function</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="SKFunction"/>.</returns>
    public static SKFunction FromPromptYaml(
        string text,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithNodeDeserializer(new AIRequestSettingsNodeDeserializer())
            .Build();

        var promptFunctionModel = deserializer.Deserialize<PromptFunctionModel>(text);

        return SKFunctionHelper.FromPrompt(
            promptFunctionModel,
            promptTemplateFactory,
            loggerFactory);
    }
}
