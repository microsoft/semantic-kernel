// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
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
    private static readonly Regex s_roleRegex = new(@"(?<role>system|assistant|user|function):\s+", RegexOptions.Compiled);

    private readonly Template _liquidTemplate;
    private readonly Dictionary<string, object> _inputVariables;

    /// <summary>Initializes the <see cref="LiquidPromptTemplate"/>.</summary>
    /// <param name="config">Prompt template configuration</param>
    /// <exception cref="ArgumentException"><see cref="PromptTemplateConfig.TemplateFormat"/> is not <see cref="LiquidPromptTemplateFactory.LiquidTemplateFormat"/>.</exception>
    /// <exception cref="ArgumentException">The template in <paramref name="config"/> could not be parsed.</exception>
    public LiquidPromptTemplate(PromptTemplateConfig config)
    {
        if (config.TemplateFormat != LiquidPromptTemplateFactory.LiquidTemplateFormat)
        {
            throw new ArgumentException($"Invalid template format: {config.TemplateFormat}");
        }

        // Parse the template now so we can check for errors, understand variable usage, and
        // avoid having to parse on each render.
        this._liquidTemplate = Template.ParseLiquid(config.Template);
        if (this._liquidTemplate.HasErrors)
        {
            throw new ArgumentException($"The template could not be parsed:{Environment.NewLine}{string.Join(Environment.NewLine, this._liquidTemplate.Messages)}");
        }
        Debug.Assert(this._liquidTemplate.Page is not null);

        // TODO: Update config.InputVariables with any variables referenced by the template but that aren't explicitly defined in the front matter.

        // Configure _inputVariables with the default values from the config. This will be used
        // in RenderAsync to seed the arguments used when evaluating the template.
        this._inputVariables = [];
        foreach (var p in config.InputVariables)
        {
            if (p.Default is not null)
            {
                this._inputVariables[p.Name] = p.Default;
            }
        }
    }

    /// <inheritdoc/>
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
    public async Task<string> RenderAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
#pragma warning restore CS1998
    {
        Verify.NotNull(kernel);
        cancellationToken.ThrowIfCancellationRequested();

        Dictionary<string, object>? nonEmptyArguments = null;
        if (this._inputVariables.Count is > 0 || arguments?.Count is > 0)
        {
            nonEmptyArguments = new(this._inputVariables);
            if (arguments is not null)
            {
                foreach (var p in arguments)
                {
                    if (p.Value is not null)
                    {
                        nonEmptyArguments[p.Key] = p.Value;
                    }
                }
            }
        }

        var renderedResult = this._liquidTemplate.Render(nonEmptyArguments);

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
        if (splits.Length > 1)
        {
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
                sb.Append("<message role=\"").Append(splits[i]).AppendLine("\">");
                sb.AppendLine(splits[i + 1]);
                sb.AppendLine("</message>");
            }

            renderedResult = sb.ToString();
        }

        return renderedResult;
    }
}
