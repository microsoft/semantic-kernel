// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;

#pragma warning disable IDE0130 // Namespace does not match folder structure

namespace Microsoft.SemanticKernel;

/// <summary>
/// Given a prompt, that might contain references to variables and functions:
/// - Get the list of references
/// - Resolve each reference
///   - Variable references are resolved using the context variables
///   - Function references are resolved invoking those functions
///     - Functions can be invoked passing in variables
///     - Functions do not receive the context variables, unless specified using a special variable
///     - Functions can be invoked in order and in parallel so the context variables must be immutable when invoked within the template
/// </summary>
public sealed class KernelPromptTemplate : IPromptTemplate
{
    /// <summary>
    /// Constructor for PromptTemplate.
    /// </summary>
    /// <param name="templateString">Prompt template string.</param>
    /// <param name="promptTemplateConfig">Prompt template configuration</param>
    /// <param name="loggerFactory">Logger factory</param>
    public KernelPromptTemplate(string templateString, PromptTemplateConfig promptTemplateConfig, ILoggerFactory? loggerFactory = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
        this._logger = this._loggerFactory.CreateLogger(typeof(KernelPromptTemplate));
        this._templateString = templateString;
        this._promptTemplateConfig = promptTemplateConfig;
        this._parameters = new(() => this.InitParameters());
        this._blocks = new(() => this.ExtractBlocks(this._templateString));
        this._tokenizer = new TemplateTokenizer(this._loggerFactory);
    }

    /// <inheritdoc/>
    public IReadOnlyList<SKParameterMetadata> Parameters => this._parameters.Value;

    /// <inheritdoc/>
    public async Task<string> RenderAsync(Kernel kernel, ContextVariables variables, CancellationToken cancellationToken = default)
    {
        return await this.RenderAsync(this._blocks.Value, kernel, variables, cancellationToken).ConfigureAwait(false);
    }

    #region private
    private readonly ILoggerFactory _loggerFactory;
    private readonly ILogger _logger;
    private readonly string _templateString;
    private readonly PromptTemplateConfig _promptTemplateConfig;
    private readonly TemplateTokenizer _tokenizer;
    private readonly Lazy<IReadOnlyList<SKParameterMetadata>> _parameters;
    private readonly Lazy<IList<Block>> _blocks;

    private List<SKParameterMetadata> InitParameters()
    {
        // Parameters from prompt template configuration
        Dictionary<string, SKParameterMetadata> result = new(this._promptTemplateConfig.Input.Parameters.Count, StringComparer.OrdinalIgnoreCase);
        foreach (var p in this._promptTemplateConfig.Input.Parameters)
        {
            result[p.Name] = new SKParameterMetadata(p.Name)
            {
                Description = p.Description,
                DefaultValue = p.DefaultValue
            };
        }

        // Parameters from the template
        var variableNames = this._blocks.Value.Where(block => block.Type == BlockTypes.Variable).Select(block => ((VarBlock)block).Name).ToList();
        foreach (var variableName in variableNames)
        {
            if (!string.IsNullOrEmpty(variableName) && !result.ContainsKey(variableName!))
            {
                result.Add(variableName!, new SKParameterMetadata(variableName!));
            }
        }

        return result.Values.ToList();
    }

    /// <summary>
    /// Given a prompt template string, extract all the blocks (text, variables, function calls)
    /// </summary>
    /// <param name="templateText">Prompt template (see skprompt.txt files)</param>
    /// <param name="validate">Whether to validate the blocks syntax, or just return the blocks found, which could contain invalid code</param>
    /// <returns>A list of all the blocks, ie the template tokenized in text, variables and function calls</returns>
    internal IList<Block> ExtractBlocks(string? templateText, bool validate = true)
    {
        this._logger.LogTrace("Extracting blocks from template: {0}", templateText);
        var blocks = this._tokenizer.Tokenize(templateText);

        if (validate)
        {
            foreach (var block in blocks)
            {
                if (!block.IsValid(out var error))
                {
                    throw new SKException(error);
                }
            }
        }

        return blocks;
    }

    /// <summary>
    /// Given a list of blocks render each block and compose the final result.
    /// </summary>
    /// <param name="blocks">Template blocks generated by ExtractBlocks.</param>
    /// <param name="kernel">The kernel.</param>
    /// <param name="variables">The variables.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The prompt template ready to be used for an AI request.</returns>
    internal async Task<string> RenderAsync(IList<Block> blocks, Kernel kernel, ContextVariables variables, CancellationToken cancellationToken = default)
    {
        this._logger.LogTrace("Rendering list of {0} blocks", blocks.Count);
        var tasks = new List<Task<string>>(blocks.Count);
        foreach (var block in blocks)
        {
            switch (block)
            {
                case ITextRendering staticBlock:
                    tasks.Add(Task.FromResult(staticBlock.Render(variables)));
                    break;

                case ICodeRendering dynamicBlock:
                    tasks.Add(dynamicBlock.RenderCodeAsync(kernel, variables, cancellationToken));
                    break;

                default:
                    const string Error = "Unexpected block type, the block doesn't have a rendering method";
                    this._logger.LogError(Error);
                    throw new SKException(Error);
            }
        }

        var result = new StringBuilder();
        foreach (Task<string> t in tasks)
        {
            result.Append(await t.ConfigureAwait(false));
        }

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Rendered prompt: {0}", result);

        return result.ToString();
    }

    /// <summary>
    /// Given a list of blocks, render the Variable Blocks, replacing placeholders with the actual value in memory.
    /// </summary>
    /// <param name="blocks">List of blocks, typically all the blocks found in a template.</param>
    /// <param name="variables">Container of all the temporary variables known to the kernel.</param>
    /// <returns>An updated list of blocks where Variable Blocks have rendered to Text Blocks.</returns>
    internal IList<Block> RenderVariables(IList<Block> blocks, ContextVariables? variables)
    {
        this._logger.LogTrace("Rendering variables");
        return blocks.Select(block => block.Type != BlockTypes.Variable
            ? block
            : new TextBlock(((ITextRendering)block).Render(variables), this._loggerFactory)).ToList();
    }
    #endregion
}
