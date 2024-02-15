// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Annotation that decorates an {@link DefineKernelFunction} annotation to provide examples of how to use the function.
 * For example:
 * <pre><code>
 * {@literal @}DefineSKFunction(
 *    name = "add",
 *    description = "Adds two numbers together",
 *    returnType = "java.lang.Integer",
 *    returnDescription = "The sum of the two numbers",
 *    samples = {
 *        {@literal @}SKSample(inputs = "{\"number1\":1, \"number2\":2", output = "3")
 *     }
 *  )
 * public static double add(
 *       {@literal @}SKFunctionParameters(description="The first number to add", name="number1") double number1,
 *       {@literal @}SKFunctionParameters(description="The second number to add", name="number2") double number2
 *   )
 *   {
 *       return number1 + number2;
 *   }
 * </code></pre>
 */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface SKSample {
    /**
     * An example of inputs to the function.
     * @return An example of inputs to the function.
     */
    String inputs();

    /**
     * An example output of the function given the inputs.
     * @return An example output of the function given the inputs.
     */
    String output();
}
