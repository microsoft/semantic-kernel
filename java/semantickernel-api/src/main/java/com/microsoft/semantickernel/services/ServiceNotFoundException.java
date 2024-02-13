package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.exceptions.SKCheckedException;

public class ServiceNotFoundException extends SKCheckedException {

    public ServiceNotFoundException(String s) {
        super(s);
    }
}
