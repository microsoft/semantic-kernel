package com.microsoft.semantickernel.samples.syntaxexamples.javaspecific;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.orchestration.SKFunction;

import java.io.IOException;

public class Java_Example01_ResourceLoading {

    public static void main(String[] args) throws IOException {
        Kernel kernel = SKBuilders.kernel()
                .build();

        kernel.importSkillFromResources(
                "Plugins",
                "ExamplePlugins",
                "ExampleFunction",
                Java_Example01_ResourceLoading.class
        );

        SKFunction<?> function = kernel.getSkills().getFunctions("ExamplePlugins").getFunction("ExampleFunction");

        System.out.println("Loaded function: " + function.getDescription());


        kernel.importSkillFromResources(
                "Plugins",
                "ExamplePlugins",
                "ExampleFunctionRoot"
        );
        function = kernel.getSkills().getFunctions("ExamplePlugins").getFunction("ExampleFunctionRoot");

        System.out.println("Loaded function from classpath root: " + function.getDescription());


    }
}
