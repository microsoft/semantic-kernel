// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;

import java.math.BigDecimal;

/**
 * MathSkill provides a set of functions to make Math calculations.
 *
 * <ul>
 *   <li><code>input</code> is the first number in the operation.
 *   <li><code>amount</code> is the second number in the operation.
 * </ul>
 *
 * <p>Usage:
 *
 * <blockquote>
 *
 * <pre>
 * kernel.ImportSkill("math", new MathSkill());
 *
 * {{math.add}}         => Returns the sum of input and amount
 * {{math.subtract}}    => Returns the differentce of input from amount
 * </pre>
 *
 * </blockquote>
 *
 * <p>This skill uses BigDecimal to perform the number conversion and the calculations.
 */
public class MathSkill {

    /**
     * Returns the addition result of input and amount values provided.
     *
     * <p>This skill attempts to convert the numbers to BigDecimal and then add them.
     *
     * <p>If a conversion error occurs, the skill will throw an exception.
     *
     * @param input Initial value as string to add the specified amount
     * @param amount The amount to be added to input
     * @return The resulting sum as a String.
     */
    @DefineSKFunction(description = "Adds amount to a value.", name = "add")
    public String add(
            @SKFunctionInputAttribute(description = "The value to add to.") String input,
            @SKFunctionParameters(name = "amount", description = "The amount to be added to value.")
                    String amount) {

        BigDecimal bValue = new BigDecimal(input);

        return bValue.add(new BigDecimal(amount)).toString();
    }

    /**
     * Returns the subtraction result of input and amount values provided.
     *
     * <p>This skill attempts to convert the numbers to BigDecimal and then subtract them.
     *
     * <p>If a conversion error occurs, the skill will throw an exception.
     *
     * @param input Initial value as string to subtract the specified amount
     * @param amount The amount to be subtracted from input
     * @return The resulting difference as a String.
     */
    @DefineSKFunction(description = "Subtracts amount from value.", name = "Subtract")
    public String subtract(
            @SKFunctionInputAttribute(description = "The value to subtract from.") String input,
            @SKFunctionParameters(
                            name = "amount",
                            description = "The amount to be subtracted from value.")
                    String amount) {

        BigDecimal bValue = new BigDecimal(input);

        return bValue.subtract(new BigDecimal(amount)).toString();
    }
}
