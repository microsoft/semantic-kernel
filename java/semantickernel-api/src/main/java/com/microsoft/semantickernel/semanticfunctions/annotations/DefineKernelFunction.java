// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Annotation that defines a method that can be invoked as a native function
 */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface DefineKernelFunction {

    /**
     * The description of what the function does. The description should be short and concise. The
     * model uses the description to determine whether the function is a good match for use to
     * complete a prompt. If the model is not selecting a function when it should be, consider
     * adding more detail to the description.
     *
     * @return the description of the function, or an empty string if no description is provided.
     */
    String description() default "";

    /**
     * The name of the function.
     *
     * @return the name of the function, or an empty string if no name is provided.
     */
    String name() default "";

    /**
     * The fully qualified class name of the return value of the function, for example,
     * "java.lang.String". If this parameter is not provided, the model will attempt to infer the
     * return type from the method signature.
     *
     * @return the fully qualified class name of the return value of the function
     */
    String returnType() default "";

    /**
     * The description of the return value of the function. The description should be short and
     * concise.
     *
     * @return the description of the return value of the function, or an empty string if no
     * description is provided.
     */
    String returnDescription() default "";

    /**
     * Examples of how to use the function. The examples should be short and concise. The Semantic
     * Kernel can use the examples to help the model understand how the function is used.
     *
     * @return Examples of how to use the function, or an empty array if no examples are provided.
     */

    SKSample[] samples() default {};
}
