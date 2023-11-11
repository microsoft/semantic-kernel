// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// Implementation of <see cref="IPromptTemplateFactory"/> which aggregates multiple prompt template factories.
/// </summary>
public class AggregatorPromptTemplateFactory : IPromptTemplateFactory
{
    private readonly IPromptTemplateFactory[] _promptTemplateFactories;

    /// <summary>
    /// Constructor for <see cref="AggregatorPromptTemplateFactory"/>.
    /// </summary>
    /// <param name="promptTemplateFactories">List of <see cref="IPromptTemplateFactory"/> instances</param>
    public AggregatorPromptTemplateFactory(params IPromptTemplateFactory[] promptTemplateFactories)
    {
        Verify.NotNull(promptTemplateFactories);

        if (promptTemplateFactories.Length == 0)
        {
            throw new SKException("At least one prompt template factory must be specified.");
        }

        this._promptTemplateFactories = promptTemplateFactories;
    }

    /// <summary>
    /// Create an instance of <see cref="IPromptTemplate"/> from a template string and a configuration. Throws an <see cref="SKException"/> if the specified template format is not supported.
    /// </summary>
    /// <param name="templateString">Template string using the format associated with this <see cref="IPromptTemplateFactory"/></param>
    /// <param name="promptTemplateConfig">Prompt template configuration</param>
    /// <returns></returns>
    public IPromptTemplate Create(string templateString, PromptTemplateConfig promptTemplateConfig)
    {
        foreach (var promptTemplateFactory in this._promptTemplateFactories)
        {
            try
            {
                var promptTemplate = promptTemplateFactory.Create(templateString, promptTemplateConfig);
                if (promptTemplate != null)
                {
                    return promptTemplate;
                }
            }
            catch (SKException)
            {
                // Ignore the exception and try the next factory
            }
        }

        throw new SKException($"Prompt template format {promptTemplateConfig.TemplateFormat} is not supported.");
    }

    private static IPromptTemplateFactory? s_promptTemplateFactory;

    /// <summary>
    /// Create an instance of <see cref="IPromptTemplateFactory"/> using implementations from current domain.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    public static IPromptTemplateFactory CreateDefaultPromptTemplateFactory(IKernel kernel)
    {
#pragma warning disable CS0618 // Type or member is obsolete
        if (kernel.PromptTemplateEngine is not null)
        {
            return new PromptTemplateFactory(kernel.PromptTemplateEngine);
        }
#pragma warning restore CS0618 // Type or member is obsolete

        if (s_promptTemplateFactory is null)
        {
            var appDomain = AppDomain.CurrentDomain;
            var assemblies = appDomain.GetAssemblies();
            var type = typeof(IPromptTemplateFactory);
            var types = assemblies.SelectMany(a => a.GetTypes())
                .Where(t => type.IsAssignableFrom(t)
                    && !t.IsInterface
                    && !t.IsAbstract
                    && t.GetConstructor(new Type[] { typeof(ILoggerFactory) }) != null);
            var factories = types.Select(t => (IPromptTemplateFactory)Activator.CreateInstance(t, kernel.LoggerFactory)).ToArray();

            s_promptTemplateFactory = new AggregatorPromptTemplateFactory(factories);
        }

        return s_promptTemplateFactory;
    }

    #region Obsolete
    [Obsolete("IPromptTemplateEngine is being replaced with IPromptTemplateFactory. This will be removed in a future release.")]
    internal sealed class PromptTemplateFactory : IPromptTemplateFactory
    {
        private readonly IPromptTemplateEngine _promptTemplateEngine;

        public PromptTemplateFactory(IPromptTemplateEngine promptTemplateEngine)
        {
            this._promptTemplateEngine = promptTemplateEngine;
        }

        public IPromptTemplate Create(string templateString, PromptTemplateConfig promptTemplateConfig)
        {
            return new PromptTemplate(templateString, promptTemplateConfig, this._promptTemplateEngine);
        }
    }
    #endregion
}
