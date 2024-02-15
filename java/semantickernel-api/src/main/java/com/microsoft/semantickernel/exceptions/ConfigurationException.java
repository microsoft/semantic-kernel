// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.exceptions;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * An exception that is thrown when there is an error with the 
 * Semantic Kernel configuration.
 */
public class ConfigurationException extends SKCheckedException {

    @Nonnull
    private final ErrorCodes errorCode;

    /**
     * Creates a new instance of the {@link ConfigurationException} class.
     * @param error the error code
     */
    public ConfigurationException(@Nonnull ErrorCodes error) {
        this(error, null, null);
    }

    /**
     * Creates a new instance of the {@link ConfigurationException} class.
     * @param errorCode the error code
     * @param message the message
     */
    public ConfigurationException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

    /**
     * Creates a new instance of the {@link ConfigurationException} class.
     * @param errorCode the error code
     * @param message the message
     * @param innerException the inner exception
     */
    public ConfigurationException(
        @Nonnull ErrorCodes errorCode,
        @Nullable String message,
        @Nullable Throwable innerException) {
        super(formatDefaultMessage(errorCode.getMessage(), message), innerException);
        this.errorCode = errorCode;
    }

    /**
     * Gets the error code.
     * @return the error code
     */
    public ErrorCodes getErrorCode() {
        return errorCode;
    }

    /**
     * ErrorCodes for this exception.
     */
    public enum ErrorCodes {
        /** Unknown error */
        UNKNOWN_ERROR("Unknown error"),

        /** Could not find configuration file */
        CONFIGURATION_NOT_FOUND("Could not find configuration file"),

        /** Could not parse or load configuration file */
        COULD_NOT_READ_CONFIGURATION("Could not parse or load configuration file"),

        /** Could not find any valid configuration settings */
        NO_VALID_CONFIGURATIONS_FOUND("Could not find any valid configuration settings"),

        /** Could not find value for configuration key */
        VALUE_NOT_FOUND("Could not find value for configuration key");

        private final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        /**
         * Gets the message for the error code.
         * @return the message for the error code
         */
        public String getMessage() {
            return message;
        }

        /**
         * Format the message with the given parameter.
         * @param param helpful information
         * @return the formatted message
         */
        public String getMessage(String param) {
            return String.format(message, param);
        }
    }
}
