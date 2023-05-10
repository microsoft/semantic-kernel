// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.ReadOnlySKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;

/**
 * Pass this to Kernel.registerSemanticFunction to instantiate the function
 *
 * @param <RequestConfiguration>
 */
public abstract class SemanticFunctionDefinition<
        RequestConfiguration,
        ContextType extends ReadOnlySKContext<ContextType>,
        Result extends SKFunction<RequestConfiguration, ContextType>> {

    protected abstract SKFunction<RequestConfiguration, ContextType> build(Kernel kernel);

    /**
     * Registers the function on the given kernel and returns an instantiated function
     *
     * @param kernel
     * @return
     */
    public final Result registerOnKernel(Kernel kernel) {
        return kernel.registerSemanticFunction(this);
    }

    /**
     * Simple wrapper for creating a SemanticFunctionBuilder from a SemanticSKFunction, i.e:
     *
     * <pre>
     *     SemanticFunctionBuilder<FunctionSettings> builder = SemanticFunctionBuilder.of(
     *                 (kernel) -> {
     *                     // Build function
     *                     return new MySKFunction(....);
     *                 });
     *
     *         SemanticSKFunction<FunctionSettings> function = builder.registerOnKernel(kernel);
     *
     *         function.invokeAsync("some input");
     * </pre>
     *
     * @param func
     * @return
     * @param <T>
     */

    /*
    public static <T, ContextType extends ReadOnlySKContext<ContextType>> SemanticFunctionBuilder<T,ContextType> of(Function<Kernel, SemanticSKFunction<T,ContextType>> func) {
        return new SemanticFunctionBuilder<T,ContextType>() {
            @Override
            protected SemanticSKFunction<T,ContextType> build(Kernel kernel) {
                return func.apply(kernel);
            }
        };
    }

     */

    /**
     * Registers the function on the given kernel and returns an instantiated function
     *
     * @param kernel
     * @return
     */
    /*
    public <Result extends SemanticSKFunction<T, ContextType>> Result registerOnKernel(Kernel kernel) {
        return kernel.registerSemanticFunction(this);
    }

     */
}
