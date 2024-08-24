// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
<<<<<<< HEAD
import com.microsoft.semantickernel.textcompletion.CompletionType;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import reactor.core.publisher.Flux;
=======
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import java.util.Collections;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import reactor.core.publisher.Mono;
>>>>>>> main

public class AiServiceRegistryTest {

    @Test
    public void registeredServicesAreAvailableInTheKernel() {
        runFunctionWithAiService(true);
    }

    @Test
    public void singleServiceIsRegisteredAsDefault() {
        runFunctionWithAiService(false);
    }

    private static void runFunctionWithAiService(boolean setAsDefault) {
        KernelConfig config = SKBuilders.kernelConfig().build();
        TextCompletion service = Mockito.mock(TextCompletion.class);
<<<<<<< HEAD
        Mockito.when(service.defaultCompletionType()).thenReturn(CompletionType.STREAMING);
        Mockito.when(service.completeStreamAsync(Mockito.any(), Mockito.any()))
                .thenReturn(Flux.just("foo"));
=======
        Mockito.when(service.completeAsync(Mockito.any(), Mockito.any()))
                .thenReturn(Mono.just(Collections.singletonList("foo")));
>>>>>>> main

        Kernel kernel =
                SKBuilders.kernel()
                        .withAIService("a-service", serv<<<<<<<+beeed7b7a795d8c
<<<<<<< HEAD
        Mockito.when(service.defaultCompletionType()).thenReturn(CompletionType.STREAMING);
        Mockito.when(service.completeStreamAsync(Mockito.any(), Mockito.any()))
                .thenReturn(Flux.just("foo"));
=======
        Mockito.when(service.completeAsync(Mockito.any(), Mockito.any()))
                .thenReturn(Mono.just(Collections.singletonList("foo")));
class);

        function.invokeAsync("time travel to dinosaur age").block();

<<<<<<< HEAD
        Mockito.verify(service, Mockito.times(1)).completeStreamAsync(Mockito.any(), Mockito.any());
=======
        Mockito.verify(service, Mockito.times(1)).completeAsync(Mockito.any(), Mockito.any());
>>>>>>> main
    }

    @Test
    public void noServiceThrowsAnError() {
        KernelConfig config = SKBuilders.kernelConfig().build();

        Kernel kernel = SKBuilders.kernel().withConfiguration(config).build();

        Assertions.assertThrows(
                KernelException.class, () -> kernel.getService("a-service", TextCompletion.class));

        Assertions.assertThrows(
                KernelException.class,
                () -> {
                    CompletionSKFunction function =
                            kernel.importSkillFromDirectory("FunSkill", "../../samples/skills")
                                    .getFunction("joke", CompletionSKFunction.class);

                    function.invokeAsync("time travel to dinosaur age").block();
                });
    }
}
