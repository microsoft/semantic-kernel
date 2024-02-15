package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionMetadata;
import com.microsoft.semantickernel.orchestration.contextvariables.CaseInsensitiveMap;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import javax.annotation.Nullable;

/**
 * A collection of {@link KernelPlugin} instances.
 */
class KernelPluginCollection {

    private static final Logger LOGGER = LoggerFactory.getLogger(KernelPluginCollection.class);

    private final Map<String, KernelPlugin> plugins = new CaseInsensitiveMap<>();

    /**
     * Initialize a new instance of the {@link KernelPluginCollection} 
     * class with an empty collection of plugins.
     */
    KernelPluginCollection() {
    }

    /**
     * Initialize a new instance of the {@link KernelPluginCollection} 
     * class from a collection of plugins.
     */
    KernelPluginCollection(List<KernelPlugin> plugins) {
        plugins.forEach(plugin -> this.plugins.put(plugin.getName(), plugin));
    }

    /**
     * Gets the function with the given name from the plugin with the given name.
     * @param pluginName The name of the plugin containing the function.
     * @param functionName The name of the function to get.
     * @return The function with the given name from the plugin with the given name.
     * @throws IllegalArgumentException If the plugin or function is not found.
     */
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

    /**
     * Gets all functions from all plugins.
     * @return A list of all functions from all plugins.
     */
    List<KernelFunction<?>> getFunctions() {
        return plugins.values().stream()
            .flatMap(plugin -> plugin.getFunctions().values().stream())
            .collect(Collectors.toList());
    }

    /**
     * Gets all function metadata from all plugins.
     * @return A list of all function metadata from all plugins.
     */
    List<KernelFunctionMetadata<?>> getFunctionsMetadata() {
        return plugins.values().stream()
            .flatMap(plugin -> plugin.getFunctions().values().stream())
            .map(KernelFunction::getMetadata)
            .collect(Collectors.toList());
    }

    /**
     * Gets all plugins that were added to the kernel.
     * @return The plugins available through the kernel.
     */
    Collection<KernelPlugin> getPlugins() {
        return Collections.unmodifiableCollection(plugins.values());
    }

    /**
     * Gets the plugin with the specified name.
     * @param pluginName The name of the plugin to get.
     * @return The plugin with the specified name, or {@code null} if no such plugin exists.
     */
    @Nullable
    KernelPlugin getPlugin(String pluginName) {
        return plugins.get(pluginName);
    }

    /**
     * Adds a plugin to the collection.
     * If a plugin with the same name already exists, it will be replaced.
     * @param plugin The plugin to add.
     */
    void add(KernelPlugin plugin) {
        if (plugins.containsKey(plugin.getName())) {
            LOGGER.warn("Plugin {} already exists, overwriting existing plugin", plugin.getName());
        }

        plugins.put(plugin.getName(), plugin);
    }
}
