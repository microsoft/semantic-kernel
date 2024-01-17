// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import java.util.function.Supplier;

public interface DefaultTextCompletionSupplier extends Supplier<TextCompletion> {

    public static TextCompletion getInstance(Kernel kernel) {
        return kernel.getService(null, TextCompletion.class);
    }
}
