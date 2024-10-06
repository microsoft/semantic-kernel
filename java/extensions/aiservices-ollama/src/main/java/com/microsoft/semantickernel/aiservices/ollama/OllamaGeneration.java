package com.microsoft.semantickernel.aiservices.ollama;

import java.util.List;
import java.util.Map;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.aiservices.AIService;
import com.microsoft.semantickernel.aiservices.responsetypes.BinaryFile;

import reactor.core.publisher.Mono;

public class OllamaGeneration implements AIService {

    public OllamaGeneration(String modelId) {}
    
    @Override
    public String getModelId() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getModelId'");
    }

    @Override
    public List<Class<?>> getOutputTypes() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getOutputTypes'");
    }

    @Override
    public List<String> getCapabilities() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getCapabilities'");
    }

    @Override
    public Mono<FunctionResult> getModelResultAsync(Kernel kernel, String pluginName, String name, String prompt,
            Map<Object, BinaryFile> files) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getModelResultAsync'");
    }

    @Override
    public Mono<FunctionResult> getModelStreamingResultAsync(Kernel kernel, String pluginName, String name,
            String prompt, Map<Object, BinaryFile> files) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getModelStreamingResultAsync'");
    }
    
}
