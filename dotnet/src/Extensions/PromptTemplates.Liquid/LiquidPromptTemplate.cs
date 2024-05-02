// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Web;
using Scriban;

namespace Microsoft.SemanticKernel.PromptTemplates.Liquid;

internal sealed class LiquidPromptTemplate : IPromptTemplate
{
    private const string ReservedString = "&#58;";
    private const string ColonString = ":";
    private readonly PromptTemplateConfig _config;
    private readonly bool _allowUnsafeContent;
    private static readonly Regex s_roleRegex = new(@"(?<role>system|assistant|user|function):[\s]+");

    public LiquidPromptTemplate(PromptTemplateConfig config, bool allowUnsafeContent = false)
    {
        if (config.TemplateFormat != LiquidPromptTemplateFactory.LiquidTemplateFormat)
        {
            throw new ArgumentException($"Invalid template format: {config.TemplateFormat}");
        }

        this._allowUnsafeContent = allowUnsafeContent;
        this._config = config;
    }

    public Task<string> RenderAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);

        var template = this._config.Template;
        //template = this.PreProcessTemplate(template);
        var liquidTemplate = Template.ParseLiquid(template);
        arguments = this.GetVariables(arguments);
        var renderedResult = liquidTemplate.Render(arguments.ToDictionary(kv => kv.Key, kv => kv.Value));

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
            content = this.ReplaceReservedStringBackToColonIfNeeded(content);
            sb.Append("<message role=\"").Append(role).AppendLine("\">");
            sb.AppendLine(content);
            sb.AppendLine("</message>");
        }

        renderedResult = sb.ToString();
        return Task.FromResult(renderedResult);
    }

    /// <summary>
    /// Pre-process the template before rendering.
    /// If the template contains any reserved characters and <see cref="_allowUnsafeContent"/> is false,
    /// throw an exception.
    ///
    /// Otherwise, no pre-processing is needed.
    /// </summary>
    /// <param name="template">template</param>
    /// <returns>Preprocessed template</returns>
    private string PreProcessTemplate(string template)
    {
        if (this._allowUnsafeContent)
        {
            return template;
        }

        if (template.Contains(ReservedString))
        {
            var errorMessage = $"Template contains reserved character: {ReservedString}, either remove the character or set {nameof(this._allowUnsafeContent)} to true.";
            throw new ArgumentException(errorMessage);
        }

        return template;
    }

    private string ReplaceReservedStringBackToColonIfNeeded(string text)
    {
        if (this._allowUnsafeContent)
        {
            return text;
        }

        return text.Replace(ReservedString, ColonString);
    }

    /// <summary>
    /// Gets the variables for the prompt template, including setting any default values from the prompt config.
    /// </summary>
    private KernelArguments GetVariables(KernelArguments? arguments)
    {
        KernelArguments result = [];

        foreach (var p in this._config.InputVariables)
        {
            if (p.Default == null || (p.Default is string stringDefault && stringDefault.Length == 0))
            {
                continue;
            }

            result[p.Name] = p.Default;
        }

        if (arguments is not null)
        {
            foreach (var kvp in arguments)
            {
                if (kvp.Value is not null)
                {
                    var value = (object)kvp.Value;
                    if (this.ShouldEncode(value))
                    {
                        var valueString = value.ToString();
                        valueString = HttpUtility.HtmlEncode(valueString);
                        if (this.ShouldEncodeColon(this._config, kvp.Key, kvp.Value))
                        {
                            valueString = valueString.Replace(ColonString, ReservedString);
                        }
                        result[kvp.Key] = valueString;
                    }
                    else
                    {
                        result[kvp.Key] = value;
                    }
                }
            }
        }

        return result;
    }

    private bool ShouldEncode(object? propertyValue)
    {
        if (propertyValue is null || propertyValue is not string)
        {
            return false;
        }

        return true;
    }

    private bool ShouldEncodeColon(PromptTemplateConfig promptTemplateConfig, string propertyName, object? propertyValue)
    {
        if (propertyValue is null || propertyValue is not string || this._allowUnsafeContent)
        {
            return false;
        }

        foreach (var inputVariable in promptTemplateConfig.InputVariables)
        {
            if (inputVariable.Name == propertyName)
            {
                return !inputVariable.AllowUnsafeContent;
            }
        }

        return true;
    }
}
