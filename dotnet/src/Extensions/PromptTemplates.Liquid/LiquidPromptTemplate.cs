// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Scriban;

namespace Microsoft.SemanticKernel.PromptTemplates.Liquid;

/// <summary>
/// Represents a Liquid prompt template.
/// </summary>
internal sealed class LiquidPromptTemplate : IPromptTemplate
{
    private readonly PromptTemplateConfig _config;
    private static readonly Regex s_roleRegex = new(@"(?<role>system|assistant|user|function):[\s]+");

    /// <summary>
    /// Constructor for Liquid PromptTemplate.
    /// </summary>
    /// <param name="config">Prompt template configuration</param>
    /// <exception cref="ArgumentException">throw if <see cref="PromptTemplateConfig.TemplateFormat"/> is not <see cref="LiquidPromptTemplateFactory.LiquidTemplateFormat"/></exception>
    public LiquidPromptTemplate(PromptTemplateConfig config)
    {
        if (config.TemplateFormat != LiquidPromptTemplateFactory.LiquidTemplateFormat)
        {
            throw new ArgumentException($"Invalid template format: {config.TemplateFormat}");
        }

        this._config = config;
    }

    /// <inheritdoc/>
    public Task<string> RenderAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);

        var template = this._config.Template;
        var liquidTemplate = Template.ParseLiquid(template);
        Dictionary<string, object> nonEmptyArguments = new();
        foreach (var p in this._config.InputVariables)
        {
            if (p.Default is null || (p.Default is string s && string.IsNullOrWhiteSpace(s)))
            {
                continue;
            }

            nonEmptyArguments[p.Name] = p.Default;
        }

        foreach (var p in arguments ?? new KernelArguments())
        {
            if (p.Value is null)
            {
                continue;
            }

            nonEmptyArguments[p.Key] = p.Value;
        }

        var renderedResult = liquidTemplate.Render(nonEmptyArguments);

        // parse chat history
        // for every text like below
        // (system|assistant|user|function):
        // xxxx
        //
        // turn it into
        // <message role="system|assistant|user|function">
        // xxxx
        // </message>

        var splits = s_roleRegex.Split(renderedResult);

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
            sb.Append("<message role=\"").Append(role).AppendLine("\">");
            sb.AppendLine(content);
            sb.AppendLine("</message>");
        }

        renderedResult = sb.ToString();

        return Task.FromResult(renderedResult);
    }
}
