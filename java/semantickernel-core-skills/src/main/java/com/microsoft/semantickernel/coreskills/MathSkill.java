// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;

import reactor.core.publisher.Mono;

import java.math.BigDecimal;

public class MathSkill {

    @DefineSKFunction(description = "Adds amount to a value.", name = "Add")
    public Mono<BigDecimal> add(
            @SKFunctionInputAttribute
                    @SKFunctionParameters(name = "input", description = "The value to add to.")
                    String input,
            @SKFunctionParameters(name = "amount", description = "The amount to be added to value.")
                    String amount) {

        BigDecimal bValue = new BigDecimal(input);

        return Mono.just(bValue.add(new BigDecimal(amount)));
    }

    @DefineSKFunction(description = "Subtracts amount from value.", name = "Subtract")
    public Mono<BigDecimal> subtract(
            @SKFunctionInputAttribute
                    @SKFunctionParameters(
                            name = "input",
                            description = "The value to subtract from.")
                    String input,
            @SKFunctionParameters(
                            name = "amount",
                            description = "The amount to be subtracted from value.")
                    String amount) {

        BigDecimal bValue = new BigDecimal(input);

        return Mono.just(bValue.subtract(new BigDecimal(amount)));
    }
}
