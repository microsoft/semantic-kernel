package com.microsoft.semantickernel.planner.handlebarsplanner;

import java.util.List;
import java.util.Map;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.skilldefinition.FunctionView;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import reactor.core.publisher.Mono;

public class HandlebarsPlan implements SKFunction {
    
    public HandlebarsPlan(Kernel kernel, List<String> templates) {
        
    }

    @Override
    @Nullable
    public FunctionView describe() {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public String getDescription() {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public String getName() {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public String getSkillName() {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public Mono<SKContext> invokeAsync() {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public Mono<SKContext> invokeAsync(String input) {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public Mono<SKContext> invokeAsync(SKContext context) {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public Mono<FunctionResult> invokeAsync(Kernel kernel, ContextVariables variables, boolean streaming) {
        return null;
    }

    @Override
    public Mono<SKContext> invokeAsync(SKContext context, @Nullable Object settings) {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public Mono<SKContext> invokeAsync(String input, SKContext context, Object settings) {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public Mono<SKContext> invokeWithCustomInputAsync(ContextVariables variables,
            @Nullable SemanticTextMemory semanticMemory, @Nullable ReadOnlySkillCollection skills) {
        // TODO Auto-generated method stub
        return null;
    }


    public Mono<FunctionResult> invokeAsync(Kernel kernel, Map<String,Object> variables) {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public String toEmbeddingString() {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public String toFullyQualifiedName() {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public String toManualString(boolean includeOutputs) {
        // TODO Auto-generated method stub
        return null;
    }


}
