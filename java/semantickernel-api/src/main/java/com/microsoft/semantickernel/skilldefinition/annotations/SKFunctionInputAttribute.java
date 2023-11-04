// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/** Annotates a parameter binding it to the "input" context variable */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.PARAMETER)
public @interface SKFunctionInputAttribute {
    String description();
}
