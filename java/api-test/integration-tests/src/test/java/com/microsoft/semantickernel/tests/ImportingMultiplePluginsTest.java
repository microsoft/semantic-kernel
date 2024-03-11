// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.tests;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

public class ImportingMultiplePluginsTest {

    @Test
    public void canImportMultiplePlugins() {
        KernelPlugin summarize = KernelPluginFactory.importPluginFromResourcesDirectory(
            "Plugins",
            "SummarizePlugin",
            "Summarize",
            null,
            String.class);

        KernelPlugin topics = KernelPluginFactory.importPluginFromResourcesDirectory(
            "Plugins",
            "SummarizePlugin",
            "Topics",
            null,
            String.class);

        KernelPlugin notegen = KernelPluginFactory.importPluginFromResourcesDirectory(
            "Plugins",
            "SummarizePlugin",
            "Notegen",
            null,
            String.class);

        Kernel kernel = Kernel.builder()
            .withPlugin(summarize)
            .withPlugin(topics)
            .withPlugin(notegen)
            .build();

        Assertions.assertEquals(3,
            kernel.getPlugin("SummarizePlugin").getFunctions().size());
        Assertions.assertEquals("Summarize",
            kernel.getPlugin("SummarizePlugin").get("Summarize").getName());
        Assertions.assertEquals("Topics",
            kernel.getPlugin("SummarizePlugin").get("Topics").getName());
        Assertions.assertEquals("Notegen",
            kernel.getPlugin("SummarizePlugin").get("Notegen").getName());

    }
}
