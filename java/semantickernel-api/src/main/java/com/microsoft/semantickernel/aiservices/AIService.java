package com.microsoft.semantickernel.aiservices;

import java.util.Collections;
import java.util.List;
import java.util.Map;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.responsetypes.BinaryFile;
import com.microsoft.semantickernel.orchestration.FunctionResult;

import reactor.core.publisher.Mono;

public interface AIService extends com.microsoft.semantickernel.services.AIService {
    
    default String getModelId() { return ""; }

    default List<Class<?>> getOutputTypes() { return Collections.emptyList(); }

    default List<String> getCapabilities() { return Collections.emptyList(); }

    default Mono<FunctionResult> getModelResultAsync(Kernel kernel, String pluginName, String name, String prompt, Map<Object, BinaryFile> files) {
        return Mono.empty();
    }

    default Mono<FunctionResult> getModelStreamingResultAsync(Kernel kernel, String pluginName, String name, String prompt, Map<Object, BinaryFile> files) {
        return Mono.empty();
    }
    
}
