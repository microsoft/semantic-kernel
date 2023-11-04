// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/** Annotates a parameter to a native function */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.PARAMETER)
public @interface SKFunctionParameters {

    String NO_DEFAULT_VALUE = "SKFunctionParameters__NO_INPUT_PROVIDED";

    String description() default "";

    String name();

    String defaultValue() default NO_DEFAULT_VALUE;

    /**
     * If required is false, no value is set, and no default value is provided, null will be passed
     * as this argument.
     */
    boolean required() default true;

    Class<?> type() default String.class;
}
