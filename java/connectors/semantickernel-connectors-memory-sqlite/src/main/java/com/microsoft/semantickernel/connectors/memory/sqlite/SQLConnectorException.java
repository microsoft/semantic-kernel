// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.sqlite;

import com.microsoft.semantickernel.SKException;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** Exception thrown by the SQLite connector. */
public class SQLConnectorException extends SKException {

  private final ErrorCodes errorCode;

  /**
   * Create an exception with a message
   *
   * @param errorCode The error code
   */
  public SQLConnectorException(@Nonnull ErrorCodes errorCode) {
    this(errorCode, null, null);
  }

  /**
     * Create an exception with a message
     *
     * @param message a description of the cause of the exception
     */
    public SQLConnectorException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
      this(errorCode, message, null);
    }

    /**
     * Create an exception with a message and a cause
     *
     * @param errorCode the error code
     * @param message a description of the cause of the exception
     * @param cause the cause of the exception
     */
    public SQLConnectorException(@Nonnull ErrorCodes errorCode, @Nullable String message, @Nullable Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    public ErrorCodes getErrorCode() {
      return errorCode;
    }

    public enum ErrorCodes {
      SQL_ERROR("SQL error");

      final String message;

      ErrorCodes(String message) {
        this.message = message;
      }

      public String getMessage() {
        return message;
      }
    }
}
