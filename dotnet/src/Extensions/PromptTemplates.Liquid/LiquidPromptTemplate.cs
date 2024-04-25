// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Scriban;

namespace Microsoft.SemanticKernel.PromptTemplates.Liquid;
internal sealed class LiquidPromptTemplate : IPromptTemplate
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

        // parse chat history
        // for every text like below
        // (system|assistant|user|function):
        // xxxx
        //
        // turn it into
        // <Message role="system|assistant|user|function">
        // xxxx
        // </Message>

        var roleRegex = new Regex(@"(?<role>system|assistant|user|function):[\s]+");
        var splits = roleRegex.Split(renderedResult);

        // if no role is found, return the entire text
        if (splits.Length == 1)
        {
            return Task.FromResult(renderedResult);
        }

        // otherwise, the split text chunks will be in the following format
        // [0] = ""
        // [1] = role information
        // [2] = message content
        // [3] = role information
        // [4] = message content
        // ...
        // we will iterate through the array and create a new string with the following format
        var sb = new StringBuilder();
        for (var i = 1; i < splits.Length; i += 2)
        {
            var role = splits[i];
            var content = splits[i + 1];
            sb.AppendLine($"<Message role=\"{role}\">");
            sb.AppendLine(content);
            sb.AppendLine("</Message>");
        }

        renderedResult = sb.ToString();

        return Task.FromResult(renderedResult);
    }
}
