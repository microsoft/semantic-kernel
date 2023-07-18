// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;

namespace Microsoft.SemanticKernel.TemplateEngine;

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
public class PromptTemplateEngine : IPromptTemplateEngine
{
    private readonly ILogger _log;

    private readonly TemplateTokenizer _tokenizer;

    public PromptTemplateEngine(ILogger? log = null)
    {
        this._log = log ?? NullLogger.Instance;
        this._tokenizer = new TemplateTokenizer(this._log);
    }

    /// <inheritdoc/>
    public IList<Block> ExtractBlocks(string? templateText, bool validate = true)
    {
        this._log.LogTrace("Extracting blocks from template: {0}", templateText);
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

    /// <inheritdoc/>
    public async Task<string> RenderAsync(string templateText, SKContext context)
    {
        this._log.LogTrace("Rendering string template: {0}", templateText);
        var blocks = this.ExtractBlocks(templateText);
        return await this.RenderAsync(blocks, context).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<string> RenderAsync(IList<Block> blocks, SKContext context)
    {
        this._log.LogTrace("Rendering list of {0} blocks", blocks.Count);
        var tasks = new List<Task<string>>(blocks.Count);
        foreach (var block in blocks)
        {
            switch (block)
            {
                case ITextRendering staticBlock:
                    tasks.Add(Task.FromResult(staticBlock.Render(context.Variables)));
                    break;

                case ICodeRendering dynamicBlock:
                    tasks.Add(dynamicBlock.RenderCodeAsync(context));
                    break;

                default:
                    const string Error = "Unexpected block type, the block doesn't have a rendering method";
                    this._log.LogError(Error);
                    throw new SKException(Error);
            }
        }

        var result = new StringBuilder();
        foreach (Task<string> t in tasks)
        {
            result.Append(await t.ConfigureAwait(false));
        }

        // TODO: remove PII, allow tracing prompts differently
        this._log.LogDebug("Rendered prompt: {0}", result);
        return result.ToString();
    }

    /// <inheritdoc/>
    public IList<Block> RenderVariables(IList<Block> blocks, ContextVariables? variables)
    {
        this._log.LogTrace("Rendering variables");
        return blocks.Select(block => block.Type != BlockTypes.Variable
            ? block
            : new TextBlock(((ITextRendering)block).Render(variables), this._log)).ToList();
    }
}
