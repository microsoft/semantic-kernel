// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services;

public interface AIServiceSupplier {

    <T extends AIService> T get(String serviceId, Class<T> clazz);
}
