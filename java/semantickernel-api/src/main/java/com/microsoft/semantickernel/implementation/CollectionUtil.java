// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.implementation;

import java.util.List;
import javax.annotation.Nullable;

public class CollectionUtil {

    @Nullable
    public static <T> T getLastOrNull(
        @Nullable List<T> collection) {
        if (collection == null || collection.isEmpty()) {
            return null;
        }

        return collection.get(collection.size() - 1);
    }
}
