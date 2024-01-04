package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.CaseInsensitiveMap;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class KernelPluginCollection implements Iterable<KernelPlugin> {

    private static final Logger LOGGER = LoggerFactory.getLogger(KernelPluginCollection.class);

    private final Map<String, KernelPlugin> plugins = new CaseInsensitiveMap<>();

    public KernelPluginCollection() {
        this(Collections.emptyList());
    }

    public KernelPluginCollection(List<KernelPlugin> plugins) {
        plugins.forEach(plugin -> this.plugins.put(plugin.getName(), plugin));
    }

    @Nullable
    public KernelFunction getFunction(String pluginName, String functionName) {
        KernelPlugin plugin = plugins.get(pluginName);
        if (plugin == null) {
            LOGGER.warn("Failed to find plugin '{}'", pluginName);
            return null;
        }
        KernelFunction function = plugin.get(functionName);

        if (function == null) {
            throw new IllegalArgumentException(
                "Function '" + functionName + "' not found in plugin '" + pluginName + "'");
        }
        return function;
    }

    @Override
    public Iterator<KernelPlugin> iterator() {
        return plugins.values().iterator();
    }

    public void add(KernelPlugin plugin) {
        if (plugins.containsKey(plugin.getName())) {
            LOGGER.warn("Plugin {} already exists, overwriting existing plugin", plugin.getName());
        }

        plugins.put(plugin.getName(), plugin);
    }
}
