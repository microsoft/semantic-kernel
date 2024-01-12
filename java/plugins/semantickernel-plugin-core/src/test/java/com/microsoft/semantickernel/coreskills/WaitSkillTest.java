// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import java.time.Duration;
import org.junit.jupiter.api.Test;
import reactor.test.StepVerifier;

class WaitSkillTest {

    WaitSkill waitSkill = new WaitSkill();

    @Test
    void secondsAsync_givenPositiveSeconds_shouldDelay() {
        Duration expectedDelay = Duration.ofMillis(1500);

        String seconds = "1.5";
        StepVerifier.withVirtualTime(() -> waitSkill.wait(seconds))
                .expectSubscription()
                .expectNoEvent(expectedDelay)
                .expectComplete()
                .verify();
    }

    @Test
    void secondsAsync_givenZeroSeconds_shouldNotDelay() {
        String seconds = "0";
        StepVerifier.withVirtualTime(() -> waitSkill.wait(seconds))
                .expectSubscription()
                .expectComplete()
                .verify();
    }

    @Test
    void secondsAsync_givenNegativeSeconds_shouldNotDelay() {
        String seconds = "-1.5";
        StepVerifier.withVirtualTime(() -> waitSkill.wait(seconds))
                .expectSubscription()
                .expectComplete()
                .verify();
    }
}
