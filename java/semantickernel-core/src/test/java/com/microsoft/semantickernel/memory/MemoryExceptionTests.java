// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class MemoryExceptionTests {
    @Test
    void itRoundtripsArgsToErrorCodeCtor() {
        // Arrange
        MemoryException e =
                new MemoryException(MemoryException.ErrorCodes.FAILED_TO_CREATE_COLLECTION);

        // Assert
        assertEquals(MemoryException.ErrorCodes.FAILED_TO_CREATE_COLLECTION, e.getErrorCode());
        assertTrue(e.getMessage().contains("Failed to create collection"));
        assertNull(e.getCause());
    }

    @Test
    void itRoundtripsArgsToErrorCodeMessageCtor() {
        // Arrange
        String message = "this is a test";
        MemoryException e =
                new MemoryException(
                        MemoryException.ErrorCodes.FAILED_TO_CREATE_COLLECTION, message);

        // Assert
        assertEquals(MemoryException.ErrorCodes.FAILED_TO_CREATE_COLLECTION, e.getErrorCode());
        assertTrue(e.getMessage().contains("Failed to create collection"));
        assertTrue(e.getMessage().contains(message));
        assertNull(e.getCause());
    }

    @Test
    void itRoundtripsArgsToErrorCodeMessageExceptionCtor() {
        // Arrange
        String message = "this is a test";
        Exception inner = new NumberFormatException();
        MemoryException e =
                new MemoryException(
                        MemoryException.ErrorCodes.FAILED_TO_CREATE_COLLECTION, message, inner);

        // Assert
        assertEquals(MemoryException.ErrorCodes.FAILED_TO_CREATE_COLLECTION, e.getErrorCode());
        assertTrue(e.getMessage().contains("Failed to create collection"));
        assertTrue(e.getMessage().contains(message));
        assertSame(inner, e.getCause());
    }

    @Test
    void itAllowsNullMessageAndInnerExceptionInCtors() {
        // Arrange
        MemoryException e =
                new MemoryException(
                        MemoryException.ErrorCodes.FAILED_TO_CREATE_COLLECTION, null, null);

        // Assert
        assertEquals(MemoryException.ErrorCodes.FAILED_TO_CREATE_COLLECTION, e.getErrorCode());
        assertTrue(e.getMessage().contains("Failed to create collection"));
        assertNull(e.getCause());
    }
}
