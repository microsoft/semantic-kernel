// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.e2e;

import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIf;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

@EnabledIf("isAzureTestEnabled")
public class FunSkillTest extends AbstractKernelTest {
    private static final Logger LOGGER = LoggerFactory.getLogger(FunSkillTest.class);

    @Test
    public void tellAJoke() throws ConfigurationException {
        Mono<SKContext> result =
                buildTextCompletionKernel()
                        .importSkillFromDirectory("FunSkill", "../../../samples/skills")
                        .getFunction("joke", CompletionSKFunction.class)
                        .invokeAsync("time travel to dinosaur age");

        if (result != null) {
            LOGGER.info(result.block().getResult());
        }
    }
}
