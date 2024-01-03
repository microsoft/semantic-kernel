// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.semantickernel;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.Verify;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.semanticfunctions.InputVariable;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.templateengine.semantickernel.TemplateException.ErrorCodes;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.Block;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.BlockTypes;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.CodeRendering;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.NamedArgBlock;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.TextRendering;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.VarBlock;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/// <summary>
/// Prompt template.
/// </summary>
public class DefaultPromptTemplate implements PromptTemplate {

    @Nullable
    private PromptTemplateConfig promptTemplate;

    public DefaultPromptTemplate() {
        this(null);
    }

    public DefaultPromptTemplate(
        @Nullable PromptTemplateConfig promptTemplate) {
        this.promptTemplate = promptTemplate;
    }

    /// <summary>
    /// Given a prompt template string, extract all the blocks (text, variables, function calls)
    /// </summary>
    /// <returns>A list of all the blocks, ie the template tokenized in text, variables and function calls</returns>
    private List<Block> extractBlocks() {
        String templateText = promptTemplate.getTemplate();

        List<Block> blocks = new TemplateTokenizer().tokenize(templateText);

        Optional<Block> invalid = blocks
            .stream()
            .filter(block -> !block.isValid())
            .findFirst();

        if (invalid.isPresent()) {
            throw new TemplateException(ErrorCodes.SYNTAX_ERROR,
                "Invalid block: " + invalid.get().getContent());
        }

        return blocks;
    }


    /// <summary>
    /// Augments <paramref name="config"/>'s <see cref="PromptTemplateConfig.InputVariables"/> with any variables
    /// not already contained there but that are referenced in the prompt template.
    /// </summary>
    private void addMissingInputVariables(List<Block> blocks) {
        if (promptTemplate == null) {
            return;
        }
        // Add all of the existing input variables to our known set. We'll avoid adding any
        // dynamically discovered input variables with the same name.
        Set<String> seen = new HashSet<>();

        seen.addAll(
            promptTemplate
                .getInputVariables()
                .stream()
                .map(InputVariable::getName)
                .collect(Collectors.toList())
        );

        blocks.forEach(block -> {
            String name = null;
            if (block.getType() == BlockTypes.Variable) {
                name = ((VarBlock) block).getName();
            } else if (block.getType() == BlockTypes.NamedArg) {
                name = ((NamedArgBlock) block).getVarBlock().getName();
            }

            if (!Verify.isNullOrEmpty(name) && !seen.contains(name)) {
                seen.add(name);
                promptTemplate.getInputVariables().add(new InputVariable(name));
            }
        });
    }

    @Override
    public Mono<String> renderAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments) {

        List<Block> blocks = this.extractBlocks();
        addMissingInputVariables(blocks);

        return Flux
            .fromIterable(blocks)
            .concatMap(block -> {
                if (block instanceof TextRendering) {
                    return Mono.just(
                        ((TextRendering) block).render(arguments)
                    );
                } else if (block instanceof CodeRendering) {
                    return ((CodeRendering) block).renderCodeAsync(kernel, arguments);
                } else {
                    return Mono.error(new TemplateException(ErrorCodes.UNEXPECTED_BLOCK_TYPE));
                }
            })
            .reduce("", (a, b) -> {
                return a + b;
            });
    }
}
