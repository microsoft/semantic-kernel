package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

public class KernelPluginCollection implements Iterable<KernelPlugin> {

    private final Map<String, KernelPlugin> plugins = new HashMap<>();

    public KernelPluginCollection() {
        this(Collections.emptyList());
    }

    public KernelPluginCollection(List<KernelPlugin> plugins) {
        plugins.forEach(plugin -> this.plugins.put(plugin.getName(), plugin));
    }

    public KernelFunction getFunction(String pluginName, String functionName) {
        KernelPlugin plugin = plugins.get(pluginName);
        if (plugin == null) {
            throw new IllegalArgumentException("Plugin '" + pluginName + "' not found");
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
            throw new IllegalArgumentException("Plugin " + plugin.getName() + " already exists");
        }

        plugins.put(plugin.getName(), plugin);
    }
}
