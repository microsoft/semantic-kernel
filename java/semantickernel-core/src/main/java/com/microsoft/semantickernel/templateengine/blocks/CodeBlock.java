// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import reactor.core.publisher.Mono;
import reactor.util.annotation.Nullable;

import java.util.Collections;
import java.util.List;

// ReSharper disable TemplateIsNotCompileTimeConstantProblem
public class CodeBlock extends Block implements CodeRendering {
    private final List<Block> tokens;

    public CodeBlock(List<Block> tokens, String content) {
        super(content, BlockTypes.Code);
        this.tokens = Collections.unmodifiableList(tokens);
    }

    public CodeBlock(String content) {
        super(content, BlockTypes.Code);
        this.tokens = null;
    }

    @Override
    public boolean isValid() {
        // TODO
        return true;
    }

    @Override
    @Nullable
    public Mono<String> renderCodeAsync(SKContext context) {
        /* TODO
        }
            if (!this._validated && !this.IsValid(out var error))
            {
                throw new TemplateException(TemplateException.ErrorCodes.SyntaxError, error);
            }

             */

        // this.Log.LogTrace("Rendering code: `{0}`", this.Content);

        switch (this.tokens.get(0).getType()) {
            case Value:
            case Variable:
                return Mono.just(
                        ((TextRendering) this.tokens.get(0)).render(context.getVariables()));

            case FunctionId:
                return this.renderFunctionCallAsync((FunctionIdBlock) this.tokens.get(0), context);
        }

        throw new RuntimeException("Unknown type");
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
            String input = ((TextRendering) this.tokens.get(1)).render(variables);

            variables = context.getVariables().writableClone().update(input);
        }

        Mono<SKContext> result =
                function.invokeWithCustomInputAsync(
                        variables, context.getSemanticMemory(), context.getSkills());

        return result.map(
                it -> {
                    return it.getResult();
                });
    }

    private SKFunction getFunctionFromSkillCollection(
            ReadOnlySkillCollection skills, FunctionIdBlock fBlock) {
        String skillName = fBlock.getSkillName();
        // Function in the global skill
        if ((skillName == null || skillName.isEmpty())
                && skills.hasFunction(fBlock.getFunctionName())) {
            SKFunction<?, ?> function =
                    skills.getFunction(fBlock.getFunctionName(), SKFunction.class);
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
