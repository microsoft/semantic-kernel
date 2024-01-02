package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelArguments;
import com.microsoft.semantickernel.KernelFunction;

public enum OrderedAIServiceSelector implements AIServiceSelector {

    INST;
    
    @Override
    public AIServiceSelection trySelectAIService(Class<? extends AIService> serviceType, Kernel kernel,
            KernelFunction function, KernelArguments arguments) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Not implemented");
    }
    
}
