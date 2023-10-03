package com.microsoft.semantickernel.samples.syntaxexamples;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.coreskills.TextSkill;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import reactor.core.publisher.Mono;

/**
 * Demonstrates running a pipeline (a sequence of functions) over some input.
 */
public class Example02_Pipeline {
    public static void main(String[] args) {
        Kernel kernel = SKBuilders.kernel().build();

        // Load native skill
        ReadOnlyFunctionCollection text = kernel.importSkill(new TextSkill(), null);

        Mono<SKContext> result =
                kernel.runAsync(
                        "    i n f i n i t e     s p a c e     ",
                        text.getFunction("LStrip"),
                        text.getFunction("RStrip"),
                        text.getFunction("Uppercase"));

        System.out.println(result.block().getResult());
    }
}
