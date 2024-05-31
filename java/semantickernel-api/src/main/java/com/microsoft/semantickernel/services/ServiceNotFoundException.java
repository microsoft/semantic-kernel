// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.exceptions.SKCheckedException;

/**
 * Exception thrown when a service is not found.
 */
public class ServiceNotFoundException extends SKCheckedException {

    /**
     * Initializes a new instance of the {@link ServiceNotFoundException} class.
     *
     * @param s A message which describes the service that could not be found.
     */
    public ServiceNotFoundException(String s) {
        super(s);
    }
}
