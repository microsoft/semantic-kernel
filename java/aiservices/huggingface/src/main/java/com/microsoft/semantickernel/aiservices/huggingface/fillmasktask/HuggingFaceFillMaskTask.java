package com.microsoft.semantickernel.aiservices.huggingface.fillmasktask;

import java.util.List;
import java.util.Map;

import com.azure.core.http.HttpClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.AIService;
import com.microsoft.semantickernel.aiservices.responsetypes.BinaryFile;
import com.microsoft.semantickernel.orchestration.FunctionResult;

import reactor.core.publisher.Mono;

public class HuggingFaceFillMaskTask implements AIService {

    public HuggingFaceFillMaskTask(String modelId, String apiKey, HttpClient httpClient, String endpoint) {}
    

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
