package com.microsoft.semantickernel;

public interface ServiceProvider {

    <T extends AIService> T getService(Class<T> clazz);
}
