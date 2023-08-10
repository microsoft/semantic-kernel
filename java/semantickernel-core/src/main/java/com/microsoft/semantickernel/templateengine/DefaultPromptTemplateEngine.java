// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine;

import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.templateengine.blocks.Block;
import com.microsoft.semantickernel.templateengine.blocks.CodeRendering;
import com.microsoft.semantickernel.templateengine.blocks.TextRendering;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/// <summary>
/// Given a prompt, that might contain references to variables and functions:
/// - Get the list of references
/// - Resolve each reference
///   - Variable references are resolved using the context variables
///   - Function references are resolved invoking those functions
///     - Functions can be invoked passing in variables
///     - Functions do not receive the context variables, unless specified using a special variable
///     - Functions can be invoked in order and in parallel so the context variables must be
// immutable when invoked within the template
/// </summary>
public class DefaultPromptTemplateEngine implements PromptTemplateEngine {
    private static final Logger LOGGER = LoggerFactory.getLogger(DefaultPromptTemplateEngine.class);

    private final TemplateTokenizer tokenizer;

    public DefaultPromptTemplateEngine() {
        tokenizer = new TemplateTokenizer();
    }

    @Override
    public List<Block> extractBlocks(String templateText) {
        return extractBlocks(templateText, true);
    }

    public List<Block> extractBlocks(String templateText, boolean validate) {
        // TODO
        // this._log.LogTrace("Extracting blocks from template: {0}", templateText);
        List<Block> blocks = this.tokenizer.tokenize(templateText);

        if (validate) {
            blocks.forEach(
                    block -> {
                        if (!block.isValid()) {
                            throw new TemplateException(TemplateException.ErrorCodes.SyntaxError);
                        }
                    });
        }

        return blocks;
    }

    /// <inheritdoc/>
    @Override
    public Mono<String> renderAsync(String templateText, SKContext context) {
        // TODO
        // this._log.LogTrace("Rendering string template: {0}", templateText);
        List<Block> blocks = this.extractBlocks(templateText);
        return this.renderAsync(blocks, context);
    }

    /// <inheritdoc/>
    public Mono<String> renderAsync(List<Block> blocks, SKContext context) {
        return Flux.fromIterable(blocks)
                .concatMap(
                        block -> {
                            if (block instanceof TextRendering) {
                                return Mono.just(
                                        ((TextRendering) block).render(context.getVariables()));
                            } else if (block instanceof CodeRendering) {
                                return ((CodeRendering) block).renderCodeAsync(context);
                            } else {
                                String message =
                                        "Unexpected block type, the block doesn't have a rendering"
                                                + " method";
                                LOGGER.error(message);
                                return Mono.error(
                                        new TemplateException(
                                                TemplateException.ErrorCodes.UnexpectedBlockType,
                                                message));
                            }
                        })
                .collectList()
                .map(
                        values -> {
                            StringBuilder sb = new StringBuilder();
                            values.forEach(sb::append);
                            return sb.toString();
                        });
        /*
        this._log.LogTrace("Rendering list of {0} blocks", blocks.Count);
        var result = new StringBuilder();
        foreach (var block in blocks)
        {
            switch (block)
            {
                case ITextRendering staticBlock:
                    result.Append(staticBlock.Render(context.Variables));
                    break;

                case ICodeRendering dynamicBlock:
                    result.Append(await dynamicBlock.RenderCodeAsync(context));
                    break;

                default:
                    const string error = "Unexpected block type, the block doesn't have a rendering method";
                    this._log.LogError(error);
                    throw new TemplateException(TemplateException.ErrorCodes.UnexpectedBlockType, error);
            }
        }

        // TODO: remove PII, allow tracing prompts differently
        this._log.LogDebug("Rendered prompt: {0}", result);
        return result.ToString();

         */
    }

    public static final class Builder extends PromptTemplateEngine.Builder {
        @Override
        public PromptTemplateEngine build() {
            return new DefaultPromptTemplateEngine();
        }
    }
}
