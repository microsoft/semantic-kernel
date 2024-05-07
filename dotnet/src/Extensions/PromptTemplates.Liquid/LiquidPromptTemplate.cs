// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Scriban;
using Scriban.Syntax;

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

        // Ideally the prompty author would have explicitly specified input variables. If they specified any,
        // assume they specified them all. If they didn't, heuristically try to find the variables, looking for
        // variables that are read but never written and that appear to be simple values rather than complex objects.
        if (config.InputVariables.Count == 0)
        {
            foreach (string implicitVariable in SimpleVariablesVisitor.InferInputs(this._liquidTemplate))
            {
                config.InputVariables.Add(new() { Name = implicitVariable, AllowUnsafeContent = config.AllowUnsafeContent });
            }
        }

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

    /// <summary>
    /// Visitor for <see cref="ScriptPage"/> looking for variables that are only
    /// ever read and appear to represent very simple strings. If any variables
    /// other than that are found, none are returned.
    /// </summary>
    private sealed class SimpleVariablesVisitor : ScriptVisitor
    {
        private readonly HashSet<string> _variables = new(StringComparer.OrdinalIgnoreCase);
        private bool _valid = true;

        public static HashSet<string> InferInputs(Template template)
        {
            var visitor = new SimpleVariablesVisitor();

            template.Page.Accept(visitor);
            if (!visitor._valid)
            {
                visitor._variables.Clear();
            }

            return visitor._variables;
        }

        public override void Visit(ScriptVariableGlobal node)
        {
            if (this._valid)
            {
                switch (node.Parent)
                {
                    case ScriptAssignExpression assign when ReferenceEquals(assign.Target, node):
                    case ScriptForStatement forLoop:
                    case ScriptMemberExpression member:
                        // Unsupported use found; bail.
                        this._valid = false;
                        return;

                    default:
                        // Reading from a simple variable.
                        this._variables.Add(node.Name);
                        break;
                }

                base.DefaultVisit(node);
            }
        }
    }
}
