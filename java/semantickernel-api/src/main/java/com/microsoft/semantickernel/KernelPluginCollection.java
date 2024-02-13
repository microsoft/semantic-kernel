package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionMetadata;
import com.microsoft.semantickernel.orchestration.contextvariables.CaseInsensitiveMap;
import com.microsoft.semantickernel.plugin.KernelPlugin;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class KernelPluginCollection {

    private static final Logger LOGGER = LoggerFactory.getLogger(KernelPluginCollection.class);

    private final Map<String, KernelPlugin> plugins = new CaseInsensitiveMap<>();

    KernelPluginCollection() {
    }

    KernelPluginCollection(List<KernelPlugin> plugins) {
        plugins.forEach(plugin -> this.plugins.put(plugin.getName(), plugin));
    }

    KernelFunction<?> getFunction(String pluginName, String functionName) {
        KernelPlugin plugin = plugins.get(pluginName);
        if (plugin == null) {
            throw new IllegalArgumentException("Failed to find plugin " + pluginName);
        }
        KernelFunction<?> function = plugin.get(functionName);

        if (function == null) {
            throw new IllegalArgumentException(
                "Function '" + functionName + "' not found in plugin '" + pluginName + "'");
        }
        return function;
    }

    List<KernelFunction<?>> getFunctions() {
        return plugins.values().stream()
            .flatMap(plugin -> plugin.getFunctions().values().stream())
            .collect(Collectors.toList());
    }

    List<KernelFunctionMetadata<?>> getFunctionsMetadata() {
        return plugins.values().stream()
            .flatMap(plugin -> plugin.getFunctions().values().stream())
            .map(KernelFunction::getMetadata)
            .collect(Collectors.toList());
    }

    List<KernelPlugin> getPlugins() {
        return new ArrayList<>(plugins.values());
    }

    KernelPlugin getPlugin(String pluginName) {
        return plugins.get(pluginName);
    }

    void add(KernelPlugin plugin) {
        if (plugins.containsKey(plugin.getName())) {
            LOGGER.warn("Plugin {} already exists, overwriting existing plugin", plugin.getName());
        }

        plugins.put(plugin.getName(), plugin);
    }
}
