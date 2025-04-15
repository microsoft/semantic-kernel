// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Web;
using Fluid;
using Fluid.Ast;

namespace Microsoft.SemanticKernel.PromptTemplates.Liquid;

/// <summary>
/// Represents a Liquid prompt template.
/// </summary>
internal sealed partial class LiquidPromptTemplate : IPromptTemplate
{
    private static readonly FluidParser s_parser = new();
    private static readonly Fluid.TemplateOptions s_templateOptions = new()
    {
        MemberAccessStrategy = new UnsafeMemberAccessStrategy() { MemberNameStrategy = MemberNameStrategies.SnakeCase },
    };

    private const string ReservedString = "&#58;";
    private const string ColonString = ":";
    private const char LineEnding = '\n';
    private readonly PromptTemplateConfig _config;
    private readonly bool _allowDangerouslySetContent;
    private readonly IFluidTemplate _liquidTemplate;
    private readonly Dictionary<string, object> _inputVariables;

#if NET
    [GeneratedRegex(@"(?<role>system|assistant|user|function|developer):\s+")]
    private static partial Regex RoleRegex();
#else
    private static Regex RoleRegex() => s_roleRegex;
    private static readonly Regex s_roleRegex = new(@"(?<role>system|assistant|user|function|developer):\s+", RegexOptions.Compiled);
#endif

    /// <summary>Initializes the <see cref="LiquidPromptTemplate"/>.</summary>
    /// <param name="config">Prompt template configuration</param>
    /// <param name="allowDangerouslySetContent">Whether to allow dangerously set content in the template</param>
    /// <exception cref="ArgumentException">throw if <see cref="PromptTemplateConfig.TemplateFormat"/> is not <see cref="LiquidPromptTemplateFactory.LiquidTemplateFormat"/></exception>
    /// <exception cref="ArgumentException">The template in <paramref name="config"/> could not be parsed.</exception>
    /// <exception cref="ArgumentNullException">throw if <paramref name="config"/> is null</exception>
    /// <exception cref="ArgumentNullException">throw if the template in <paramref name="config"/> is null</exception>
    public LiquidPromptTemplate(PromptTemplateConfig config, bool allowDangerouslySetContent = false)
    {
        Verify.NotNull(config, nameof(config));
        Verify.NotNull(config.Template, nameof(config.Template));
        if (config.TemplateFormat != LiquidPromptTemplateFactory.LiquidTemplateFormat)
        {
            throw new ArgumentException($"Invalid template format: {config.TemplateFormat}");
        }

        this._allowDangerouslySetContent = allowDangerouslySetContent;
        this._config = config;

        // Parse the template now so we can check for errors, understand variable usage, and
        // avoid having to parse on each render.
        if (!s_parser.TryParse(config.Template, out this._liquidTemplate, out string error))
        {
            throw new ArgumentException(error is not null ?
                $"The template could not be parsed:{Environment.NewLine}{error}" :
                 "The template could not be parsed.");
        }

        // Ideally the prompty author would have explicitly specified input variables. If they specified any,
        // assume they specified them all. If they didn't, heuristically try to find the variables, looking for
        // variables that are read but never written and that appear to be simple values rather than complex objects.
        if (config.InputVariables.Count == 0)
        {
            foreach (string implicitVariable in SimpleVariablesVisitor.InferInputs(this._liquidTemplate))
            {
                config.InputVariables.Add(new() { Name = implicitVariable, AllowDangerouslySetContent = config.AllowDangerouslySetContent });
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
        var variables = this.GetTemplateContext(arguments);
        var renderedResult = this._liquidTemplate.Render(variables);

        // parse chat history
        // for every text like below
        // (system|assistant|user|function):
        // xxxx
        //
        // turn it into
        // <message role="system|assistant|user|function|developer">
        // xxxx
        // </message>
        var splits = RoleRegex().Split(renderedResult);

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
                var role = splits[i];
                var content = splits[i + 1];
                content = this.Encoding(content);
                sb.Append("<message role=\"").Append(role).Append("\">").Append(LineEnding);
                sb.Append(content).Append(LineEnding);
                sb.Append("</message>").Append(LineEnding);
            }

            renderedResult = sb.ToString().TrimEnd();
        }

        return renderedResult;
    }

    #region Private
    private string Encoding(string text)
    {
        text = this.ReplaceReservedStringBackToColonIfNeeded(text);
        text = HttpUtility.HtmlEncode(text);
        return text;
    }

    private string ReplaceReservedStringBackToColonIfNeeded(string text)
    {
        if (this._allowDangerouslySetContent)
        {
            return text;
        }

        return text.Replace(ReservedString, ColonString);
    }

    /// <summary>
    /// Gets the variables for the prompt template, including setting any default values from the prompt config.
    /// </summary>
    private TemplateContext GetTemplateContext(KernelArguments? arguments)
    {
        var ctx = new TemplateContext(s_templateOptions);

        foreach (var p in this._config.InputVariables)
        {
            if (p.Default is null || (p.Default is string stringDefault && stringDefault.Length == 0))
            {
                continue;
            }

            ctx.SetValue(p.Name, p.Default);
        }

        if (arguments is not null)
        {
            foreach (var kvp in arguments)
            {
                if (kvp.Value is not null)
                {
                    var value = (object)kvp.Value;
                    if (this.ShouldReplaceColonToReservedString(this._config, kvp.Key, kvp.Value))
                    {
                        ctx.SetValue(kvp.Key, value.ToString()?.Replace(ColonString, ReservedString));
                    }
                    else
                    {
                        ctx.SetValue(kvp.Key, value);
                    }
                }
            }
        }

        return ctx;
    }

    private bool ShouldReplaceColonToReservedString(PromptTemplateConfig promptTemplateConfig, string propertyName, object? propertyValue)
    {
        if (propertyValue is null || propertyValue is not string || this._allowDangerouslySetContent)
        {
            return false;
        }

        foreach (var inputVariable in promptTemplateConfig.InputVariables)
        {
            if (inputVariable.Name == propertyName)
            {
                return !inputVariable.AllowDangerouslySetContent;
            }
        }

        return true;
    }

    /// <summary>
    /// Visitor for <see cref="IFluidTemplate"/> looking for variables that are only
    /// ever read and appear to represent very simple strings. If any variables
    /// other than that are found, none are returned. This only handles very basic
    /// cases where the template doesn't contain any more complicated constructs;
    /// the heuristic can be improved over time.
    /// </summary>
    private sealed class SimpleVariablesVisitor : AstVisitor
    {
        private readonly HashSet<string> _variables = new(StringComparer.OrdinalIgnoreCase);
        private readonly Stack<Statement> _statementStack = new();
        private bool _valid = true;

        public static HashSet<string> InferInputs(IFluidTemplate template)
        {
            var visitor = new SimpleVariablesVisitor();

            visitor.VisitTemplate(template);
            if (!visitor._valid)
            {
                visitor._variables.Clear();
            }

            return visitor._variables;
        }

        public override Statement Visit(Statement statement)
        {
            if (!this._valid)
            {
                return statement;
            }

            this._statementStack.Push(statement);
            try
            {
                return base.Visit(statement);
            }
            finally
            {
                this._statementStack.Pop();
            }
        }

        protected override Expression VisitMemberExpression(MemberExpression memberExpression)
        {
            if (memberExpression.Segments.Count == 1 && memberExpression.Segments[0] is IdentifierSegment id)
            {
                bool isValid = true;

                if (this._statementStack.Count > 0)
                {
                    switch (this._statementStack.Peek())
                    {
                        case ForStatement:
                        case AssignStatement assign when string.Equals(id.Identifier, assign.Identifier, StringComparison.OrdinalIgnoreCase):
                            isValid = false;
                            break;
                    }
                }

                if (isValid)
                {
                    this._variables.Add(id.Identifier);
                    return base.VisitMemberExpression(memberExpression);
                }
            }

            // Found something unsupported. Bail.
            this._valid = false;
            return memberExpression;
        }
    }
    #endregion
}
