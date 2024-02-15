// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions.annotations;

import com.microsoft.semantickernel.contextvariables.ContextVariableType;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/** Annotates a parameter to a native function */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.PARAMETER)
public @interface KernelFunctionParameter {

    /**
     *  A special value that is used to indicate that no default value is provided.
     */
    String NO_DEFAULT_VALUE = "SKFunctionParameters__NO_INPUT_PROVIDED";

    /**
     * The description of the parameter. The description should be short and concise. 
     * The model uses the description to determine what value to pass to the function.
     * 
     * @return the description of the parameter, or an empty string if no description is provided.
     */
    String description() default "";

    /**
     * The name of the parameter. This element is required. 
     * @return the name of the parameter, or an empty string if no name is provided.
     */
    String name();

    /**
     * The default value of the parameter. If no value is set, {@code null} will be passed as the value to this argument.
     * @return the default value of the parameter, or {@link NO_DEFAULT_VALUE} if no default value is provided.
     */
    String defaultValue() default NO_DEFAULT_VALUE;

    /**
     * Whether a value is required for this argument. If required is false, the model is free to choose 
     * whether or not to provide a value. If the model does not provide a value, the default value is used.
     * @return whether a value is required for this argument.
     */
    boolean required() default true;

    /**
     * The type of the parameter. The Semantic Kernel will use the type to find a 
     * {@link ContextVariableType}
     * to convert the value from a prompt string to the correct argument type. The type defaults to
     * {@link String} if not provided.
     * @return the type of the parameter
     */
    Class<?> type() default String.class;
}
