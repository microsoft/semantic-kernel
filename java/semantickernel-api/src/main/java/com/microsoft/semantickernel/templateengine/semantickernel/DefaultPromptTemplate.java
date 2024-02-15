// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.semantickernel;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.Verify;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
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

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * The default prompt template.
 */
public class DefaultPromptTemplate implements PromptTemplate {

    private final PromptTemplateConfig promptTemplate;

    /**
     * Create a new prompt template.
     * @param promptTemplateConfig The prompt template configuration.
     */
    public DefaultPromptTemplate(
        @Nonnull PromptTemplateConfig promptTemplateConfig) {
        this.promptTemplate = new PromptTemplateConfig(promptTemplateConfig);
    }

    /*
     * Given a prompt template string, extract all the blocks (text, variables, function calls)
     * @return A list of all the blocks, ie the template tokenized in text, variables and function calls
     */
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


    /**
     * Augments the prompt template with any variables
     * not already contained there but that are referenced in the prompt template.
     * @param blocks The blocks to search for input variables.
     */
    @SuppressWarnings("NullAway")
    private void addMissingInputVariables(List<Block> blocks) {
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
                VarBlock blockName = ((NamedArgBlock) block).getVarBlock();
                name = blockName == null ? null : blockName.getName();
            }

            if (!Verify.isNullOrEmpty(name) && !seen.contains(name)) {
                seen.add(name);
                promptTemplate.addInputVariable(new InputVariable(name));
            }
        });
    }

    @Override
    public Mono<String> renderAsync(
        Kernel kernel,
        @Nullable KernelFunctionArguments arguments,
        @Nullable InvocationContext context) {

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
                    return ((CodeRendering) block).renderCodeAsync(kernel, arguments, context);
                } else {
                    return Mono.error(new TemplateException(ErrorCodes.UNEXPECTED_BLOCK_TYPE));
                }
            })
            .reduce("", (a, b) -> {
                return a + b;
            });
    }
}
