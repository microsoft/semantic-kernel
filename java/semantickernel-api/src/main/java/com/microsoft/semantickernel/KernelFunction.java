package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.FunctionResult;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface KernelFunction {

    Mono<FunctionResult> invokeAsync(Kernel kernel, KernelArguments arguments);
    
    Flux<StreamingKernelContent> invokeStreamingAsync(Kernel kernel, KernelArguments arguments);

    
}
