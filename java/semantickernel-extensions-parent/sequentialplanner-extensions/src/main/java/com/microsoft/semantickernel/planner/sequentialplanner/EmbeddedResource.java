// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.sequentialplanner;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class EmbeddedResource {

    // private static readonly string? s_namespace = typeof(EmbeddedResource).Namespace;

    public static String read(String name) {
        try (InputStream stream = SequentialPlanner.class.getResourceAsStream(name)) {
            byte[] buffer = new byte[stream.available()];
            stream.read(buffer);
            return new String(buffer, StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        /*
        var assembly = typeof(EmbeddedResource).GetTypeInfo().Assembly;
        if (assembly == null) { throw new PlanningException(PlanningException.ErrorCodes.InvalidConfiguration, $"[{s_namespace}] {name} assembly not found"); }

        using Stream? resource = assembly.GetManifestResourceStream($"{s_namespace}." + name);
        if (resource == null) { throw new PlanningException(PlanningException.ErrorCodes.InvalidConfiguration, $"[{s_namespace}] {name} resource not found"); }

        using var reader = new StreamReader(resource);

        return reader.ReadToEnd();
         */

        // throw new RuntimeException("Not implemented");
    }
}
