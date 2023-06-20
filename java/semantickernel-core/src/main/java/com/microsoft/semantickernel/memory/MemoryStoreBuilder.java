// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

public class MemoryStoreBuilder implements MemoryStore.Builder {
    @Override
    public MemoryStore buildVolatileMemoryStore() {
        return new VolatileMemoryStore();
    }
}
