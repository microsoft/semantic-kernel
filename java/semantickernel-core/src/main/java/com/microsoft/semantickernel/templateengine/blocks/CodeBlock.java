// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks;

import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.templateengine.TemplateException;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

public final class CodeBlock extends Block implements CodeRendering {

    private static final Logger LOGGER = LoggerFactory.getLogger(CodeBlock.class);
    private final List<Block> tokens;

    public CodeBlock(List<Block> tokens, String content) {
        super(content, BlockTypes.Code);
        this.tokens = Collections.unmodifiableList(tokens);
    }

    @Override
    public boolean isValid() {
        Optional<Block> invalid = tokens.stream().filter(token -> !token.isValid()).findFirst();
        if (invalid.isPresent()) {
            LOGGER.error("Invalid block" + invalid.get().getContent());
            return false;
        }

        if (this.tokens.size() > 1) {
            if (this.tokens.get(0).getType() != BlockTypes.FunctionId) {
                LOGGER.error("Unexpected second token found: " + this.tokens.get(1).getContent());
                return false;
            }

            if (this.tokens.get(1).getType() != BlockTypes.Value
                    && this.tokens.get(1).getType() != BlockTypes.Variable) {
                LOGGER.error("Functions support only one parameter");
                return false;
            }
        }

        if (this.tokens.size() > 2) {
            LOGGER.error("Unexpected second token found: " + this.tokens.get(1).getContent());
            return false;
        }

        return true;
    }

    @Override
    public Mono<String> renderCodeAsync(SKContext context) {
        if (!this.isValid()) {
            throw new TemplateException(TemplateException.ErrorCodes.SyntaxError);
        }

        // this.Log.LogTrace("Rendering code: `{0}`", this.Content);

        switch (this.tokens.get(0).getType()) {
            case Value:
            case Variable:
                return Mono.just(
                        ((TextRendering) this.tokens.get(0)).render(context.getVariables()));

            case FunctionId:
                return this.renderFunctionCallAsync((FunctionIdBlock) this.tokens.get(0), context);

            case Undefined:
            case Text:
            case Code:
            default:
                throw new RuntimeException("Unknown type");
        }
    }

    private Mono<String> renderFunctionCallAsync(FunctionIdBlock fBlock, SKContext context) {
        // context.ThrowIfSkillCollectionNotSet();
        SKFunction function = this.getFunctionFromSkillCollection(context.getSkills(), fBlock);
        if (function == null) {
            // var errorMsg = $ "Function `{fBlock.Content}` not found";
            // this.Log.LogError(errorMsg);
            throw new RuntimeException("Function not found");
        }

        ContextVariables variables = context.getVariables();

        // If the code syntax is {{functionName $varName}} use $varName instead of $input
        // If the code syntax is {{functionName 'value'}} use "value" instead of $input
        if (this.tokens.size() > 1) {
            // TODO: PII
            // this.Log.LogTrace("Passing variable/value: `{0}`", this._tokens[1].Content);
            String content = this.tokens.get(1).getContent();
            String input = ((TextRendering) this.tokens.get(1)).render(variables);
            if (content.startsWith("$")) {
                String varName = content.substring(1);
                variables = variables.writableClone().setVariable(varName, input);
            } else variables = variables.writableClone().update(input);
        }

        Mono<SKContext> result =
                function.invokeWithCustomInputAsync(
                        variables, context.getSemanticMemory(), context.getSkills());

        return result.map(
                it -> {
                    return it.getResult();
                });
    }

    @Nullable
    private SKFunction getFunctionFromSkillCollection(
            ReadOnlySkillCollection skills, FunctionIdBlock fBlock) {
        String skillName = fBlock.getSkillName();
        // Function in the global skill
        if ((skillName == null || skillName.isEmpty())
                && skills.hasFunction(fBlock.getFunctionName())) {
            SKFunction<?> function = skills.getFunction(fBlock.getFunctionName(), SKFunction.class);
            return function;
        }

        // Function within a specific skill
        if (!(skillName == null || skillName.isEmpty())) {

            ReadOnlyFunctionCollection skill = skills.getFunctions(fBlock.getSkillName());

            if (skill != null) {
                return skill.getFunction(fBlock.getFunctionName());
            }
        }

        return null;
    }
}
