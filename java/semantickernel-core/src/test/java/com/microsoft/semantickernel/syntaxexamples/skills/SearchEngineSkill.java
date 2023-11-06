// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples.skills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import reactor.core.publisher.Mono;

public class SearchEngineSkill {

    @DefineSKFunction(description = "Append the day variable", name = "search")
    public Mono<String> search(
            @SKFunctionInputAttribute(description = "Text to search") String input) {
        return Mono.just("Gran Torre Santiago is the tallest building in South America");
    }
}
