package com.microsoft.semantickernel.aiservices;

import java.util.List;
import java.util.Map;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.aiservices.responsetypes.BinaryFile;

import reactor.core.publisher.Mono;

public interface AIService extends com.microsoft.semantickernel.services.AIService{
    String getModelId();
    List<Class<?>> getOutputTypes();
    List<String> getCapabilities();
    Mono<FunctionResult> getModelResultAsync(Kernel kernel, String pluginName, String name, String prompt, Map<Object, BinaryFile> files);
    Mono<FunctionResult> getModelStreamingResultAsync(Kernel kernel, String pluginName, String name, String prompt, Map<Object, BinaryFile> files);
    
}
