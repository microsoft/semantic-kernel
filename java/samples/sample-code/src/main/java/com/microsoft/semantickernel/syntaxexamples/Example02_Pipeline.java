package com.microsoft.semantickernel.syntaxexamples;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.coreskills.TextSkill;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import reactor.core.publisher.Mono;

public class Example02_Pipeline {
    public static void main(String[] args) {
        KernelConfig kernelConfig = SKBuilders.kernelConfig().build();
        Kernel kernel = SKBuilders.kernel().withKernelConfig(kernelConfig).build();

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
