// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;

import reactor.core.publisher.Mono;

import java.time.Duration;

/** WaitSkill provides a set of functions to wait before making the rest of operations. */
public class WaitSkill {

    /**
     * Wait for a certain number of seconds.
     *
     * <p>Examples:
     *
     * <p>SKContext context = SKBuilders.context().build();
     *
     * <p>context.setVariable("input","10");
     *
     * <p>{{wait.seconds $input}}
     *
     * @param seconds The number of seconds to wait as a string.
     * @return A Mono that completes after the specified delay.
     * @throws IllegalArgumentException If the input is not a valid number.
     */
    @DefineSKFunction(name = "seconds", description = "Wait a given amount of seconds")
    public Mono<Void> wait(String seconds) {
        try {
            double sec = Math.max(Double.parseDouble(seconds), 0);
            long milliseconds = (long) (sec * 1000);
            return Mono.delay(Duration.ofMillis(milliseconds)).then();
        } catch (NumberFormatException e) {
            return Mono.error(new IllegalArgumentException("seconds text must be a number", e));
        }
    }
}
