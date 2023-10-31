// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the namespace of IKernel
namespace Microsoft.SemanticKernel.TemplateEngine.Basic;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods associated with the the basic prompt template factory.
/// </summary>
public static class BasicPromptTemplateFactoryExtensions
{
    /// <summary>
    /// Render a template string using the basic prompt template factory.
    /// </summary>
    /// <param name="factory">BasicPromptTemplateFactory instance</param>
    /// <param name="templateString">Prompt template string.</param>
    /// <param name="context">Kernel execution context.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    public static Task<string> RenderAsync(
        this BasicPromptTemplateFactory factory,
        string templateString,
        SKContext context,
        CancellationToken cancellationToken = default)
    {
        var promptTemplate = factory.CreatePromptTemplate(templateString, new PromptTemplateConfig());
        return promptTemplate.RenderAsync(context, cancellationToken);
    }
}
