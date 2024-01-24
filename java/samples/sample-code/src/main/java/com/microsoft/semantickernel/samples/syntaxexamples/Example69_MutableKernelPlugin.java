package com.microsoft.semantickernel.samples.syntaxexamples;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.plugin.KernelFunctionFactory;
import com.microsoft.semantickernel.plugin.KernelPlugin;
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

        KernelPlugin plugin = new KernelPlugin("Plugin", "Mutable plugin", null);
        plugin.getFunctions().put("dateFunction", KernelFunctionFactory.createFromMethod(
            Time.class.getMethod("date"), new Time(), "date", null, null, null));

        Kernel kernel = Kernel.builder().build();
        kernel.getPlugins().add(plugin);

        var result = kernel.invokeAsync(kernel.getPlugins().getFunction("Plugin", "dateFunction"),
            null, String.class).block();

        System.out.println("Result: " + result.getResult());
    }
}
