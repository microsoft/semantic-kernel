// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.plugin;

import com.microsoft.semantickernel.orchestration.SKFunction;
import java.util.Collection;

public interface Plugin {
    String name();

    String description();

    Collection<SKFunction> functions();
}
