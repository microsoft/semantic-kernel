package com.microsoft.semantickernel.orchestration;

/** 
 * Represents a result from a model execution. 
 * @param <T> the type of the result object
*/
public interface ModelResult<T> {

    /** 
     * Get the raw result object stored in the {@code ModelResult} 
     * @return the raw result object
    */
    Object getRawResult();

    /** 
     * Get the result object stored in the {@code ModelResult}
     * @return the result object
    */
    T getResult();
    
}
