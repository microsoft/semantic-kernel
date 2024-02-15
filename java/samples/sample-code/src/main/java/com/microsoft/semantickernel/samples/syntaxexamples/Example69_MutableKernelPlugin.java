package com.microsoft.semantickernel.samples.syntaxexamples;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.plugin.KernelFunctionFactory;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;

public class Example69_MutableKernelPlugin {

    public static class Time {

        @DefineKernelFunction(name = "date")
        public String date() {
            return "2021-09-01";
        }
    }

    /**
     * Mutable KernelPlugin example
     * <p>
     * KernelFunction can be added directly to the function collection of the KernelPlugin by using
     * KernelPlugin.getFunctions and putting the corresponding KernelFunction
     */
    public static void main(String[] args) throws NoSuchMethodException {
        System.out.println("======== Example69_MutableKernelPlugin ========");

        KernelPlugin plugin = KernelPluginFactory.createFromObject(new Time(), "MutablePlugin");

        Kernel kernel = Kernel.builder().build();
        kernel.addPlugin(plugin);

        var result = kernel.invokeAsync(kernel.getFunction("Plugin", "dateFunction"))
            .block();

        System.out.println("Result: " + result.getResult());
    }
}
