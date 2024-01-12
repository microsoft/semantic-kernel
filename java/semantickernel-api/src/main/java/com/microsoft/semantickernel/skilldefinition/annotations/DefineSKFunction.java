// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/** Annotation that defines a method that can be invoked as a native function */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface DefineSKFunction {
    String description() default "";

    String name() default "";

    String returnType() default "void";

    String returnDescription() default "";
}
