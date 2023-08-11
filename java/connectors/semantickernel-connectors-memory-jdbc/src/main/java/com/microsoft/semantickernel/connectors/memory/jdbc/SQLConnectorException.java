// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.jdbc;

import com.microsoft.semantickernel.SKException;

/** Exception thrown by the SQLite connector. */
public class SQLConnectorException extends SKException {

    /**
     * Create an exception with a message
     *
     * @param message a description of the cause of the exception
     */
    public SQLConnectorException(String message) {
        super(message);
    }

    /**
     * Create an exception with a message and a cause
     *
     * @param message a description of the cause of the exception
     * @param cause the cause of the exception
     */
    public SQLConnectorException(String message, Throwable cause) {
        super(message, cause);
    }
}
