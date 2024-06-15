// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;
import java.nio.file.Paths;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Mono;

public class KernelPluginFactoryTest {

    public static class TestPlugin {

        @DefineKernelFunction
        public String testFunction(
            @KernelFunctionParameter(name = "input") String input) {
            return "test" + input;
        }

        @DefineKernelFunction(returnType = "int")
        public Mono<Integer> asyncTestFunction(
            @KernelFunctionParameter(name = "input") String input) {
            return Mono.just(1);
        }
    }

    @Test
    public void createFromObjectTest() {
        KernelPlugin plugin = KernelPluginFactory.createFromObject(
            new TestPlugin(),
            "test");

        Assertions.assertNotNull(plugin);
        Assertions.assertEquals(plugin.getName(), "test");
        Assertions.assertEquals(plugin.getFunctions().size(), 2);

        KernelFunction<?> testFunction = plugin.getFunctions()
            .get("testFunction");

        Assertions.assertNotNull(testFunction);
        Assertions.assertNotNull(testFunction.getMetadata().getOutputVariableType());
        Assertions.assertEquals(testFunction.getMetadata().getOutputVariableType().getType(),
            String.class);
        Assertions.assertEquals(testFunction.getMetadata().getParameters().size(), 1);
        Assertions.assertEquals(testFunction.getMetadata().getParameters().get(0).getType(),
            String.class.getName());

    }

    @Test
    public void importPluginFromDirectoryTest() {
        KernelPlugin plugin = KernelPluginFactory.importPluginFromDirectory(
            Paths.get("./src/test/resources/Plugins"),
            "ExamplePlugins",
            null);

        Assertions.assertNotNull(plugin);
        Assertions.assertEquals(plugin.getName(), "ExamplePlugins");
        Assertions.assertEquals(plugin.getFunctions().size(), 1);

        KernelFunction<?> testFunction = plugin.getFunctions()
            .get("examplefunction");

        Assertions.assertNotNull(testFunction);
        Assertions.assertNotNull(testFunction.getMetadata().getOutputVariableType());
        Assertions.assertEquals(testFunction.getMetadata().getOutputVariableType().getType(),
            String.class);
        Assertions.assertEquals(testFunction.getMetadata().getParameters().size(), 1);
        Assertions.assertEquals(testFunction.getMetadata().getParameters().get(0).getTypeClass(),
            String.class);

    }

    @Test
    public void importPluginFromResourcesDirectoryTest() {
        KernelPlugin plugin = KernelPluginFactory.importPluginFromResourcesDirectory(
            "src/test/resources/Plugins",
            "ExamplePlugins",
            "ExampleFunction",
            null);

        Assertions.assertNotNull(plugin);
        Assertions.assertEquals(plugin.getName(), "ExamplePlugins");
        Assertions.assertEquals(plugin.getFunctions().size(), 1);

        KernelFunction<?> testFunction = plugin.getFunctions()
            .get("examplefunction");

        Assertions.assertNotNull(testFunction);
        Assertions.assertNotNull(testFunction.getMetadata().getOutputVariableType());
        Assertions.assertEquals(testFunction.getMetadata().getOutputVariableType().getType(),
            String.class);
        Assertions.assertEquals(testFunction.getMetadata().getParameters().size(), 1);
        Assertions.assertEquals(testFunction.getMetadata().getParameters().get(0).getTypeClass(),
            String.class);

    }

}
