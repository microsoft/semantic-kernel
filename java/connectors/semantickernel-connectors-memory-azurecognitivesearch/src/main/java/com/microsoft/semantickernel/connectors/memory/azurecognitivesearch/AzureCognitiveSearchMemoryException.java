// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import com.microsoft.semantickernel.SKException;
import com.microsoft.semantickernel.skilldefinition.FunctionNotFound;
import com.microsoft.semantickernel.skilldefinition.FunctionNotFound.ErrorCodes;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** Exception thrown by the Azure Cognitive Search connector */
public class AzureCognitiveSearchMemoryException extends SKException {

  private final ErrorCodes errorCode;

  /**
   * Initializes a new instance of the {@code AzureCognitiveSearchMemoryException} class.
   *
   * @param errorCode Error code.
   * @param message Exception message.
   */
  public AzureCognitiveSearchMemoryException(@Nonnull ErrorCodes errorCode) {
    this(errorCode, null, null);
  }

    /**
     * Initializes a new instance of the {@code AzureCognitiveSearchMemoryException} class.
     *
     * @param errorCode Error code.
     * @param message Exception message.
     */
    public AzureCognitiveSearchMemoryException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

  /**
   * Initializes a new instance of the {@code AzureCognitiveSearchMemoryException} class.
   *
   * @param errorCode Error code.
   * @param message Exception message.
   * @param cause Cause of the exception, if any.
   */
  public AzureCognitiveSearchMemoryException(@Nonnull ErrorCodes errorCode, @Nullable String message, @Nullable Throwable cause) {
    super(formatDefaultMessage(errorCode.getMessage(), message), cause);
    this.errorCode = errorCode;
  }

    public enum ErrorCodes {
      INVALID_INDEX_NAME("Invalid index name"),
      MEMORY_NOT_FOUND("Memory not found");

      final String message;

      ErrorCodes(String message) {
        this.message = message;
      }

      public String getMessage() {
        return message;
      }
    }
}
