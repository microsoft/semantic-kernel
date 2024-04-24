// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Scriban;

namespace Microsoft.SemanticKernel.PromptTemplates.Liquid;
internal class LiquidPromptTemplate : IPromptTemplate
{
    private readonly PromptTemplateConfig _config;

    public LiquidPromptTemplate(PromptTemplateConfig config)
    {
        if (config.TemplateFormat != LiquidPromptTemplateFactory.LiquidTemplateFormat)
        {
            throw new ArgumentException($"Invalid template format: {config.TemplateFormat}");
        }

        this._config = config;
    }

    public Task<string> RenderAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        var template = this._config.Template;
        var liquidTemplate = Template.ParseLiquid(template);
        var nonEmptyArguments = arguments.Where(x => x.Value is not null).ToDictionary(x => x.Key, x => x.Value!);
        var renderedResult = liquidTemplate.Render(nonEmptyArguments);

        // post processing
        // for every system: | assistant: | user: | function:
        // replacing it with <Message role="system">, <Message role="assistant">, <Message role="user">, <Message role="function">
        return Task.FromResult(renderedResult);
    }
}
