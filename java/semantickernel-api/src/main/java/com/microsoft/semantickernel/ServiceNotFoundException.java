package com.microsoft.semantickernel;

import com.microsoft.semantickernel.exceptions.SKCheckedException;

public class ServiceNotFoundException extends SKCheckedException {

    public ServiceNotFoundException(String s) {
        super(s);
    }
}
