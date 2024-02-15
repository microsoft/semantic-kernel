package com.microsoft.semantickernel.samples.syntaxexamples;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.plugins.web.SearchUrlPlugin;

public class Example11_WebSearchQueries {

    public static void main(String[] args) {

        var kernel = Kernel.builder().build();

        // Load native plugins
        var searchUrlPlugin = KernelPluginFactory.createFromObject(new SearchUrlPlugin(),
            "SearchUrlPlugin");
        var bingSearchFunction = searchUrlPlugin.get("BingSearchUrl");

        // Run
        var ask = "What's the largest building in Europe?";
        var kernelArguments = KernelFunctionArguments.builder()
            .withVariable("query", ask)
            .build();

        var result = kernel.invokeAsync(bingSearchFunction).withArguments(kernelArguments).block();

        System.out.println(ask);
        System.out.println(result.getResult());

        /*
         * Expected output:
         * ======== WebSearchQueries ========
         * What's the tallest building in Europe?
         *
         * https://www.bing.com/search?q=What%27s%20the%20tallest%20building%20in%20Europe%3F
         * == DONE ==
         */
    }

}
