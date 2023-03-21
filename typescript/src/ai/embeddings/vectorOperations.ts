export class VectorOperations {
    /**
     * Extension method to calculate the cosine similarity between two vectors.
     *
     * https://en.wikipedia.org/wiki/Cosine_similarity
     */
    public static cosineSimilarity(x: ReadonlyArray<number>, y: ReadonlyArray<number>): number {
        if (x.length !== y.length) {
            throw new Error('Array lengths must be equal');
        }

        let dotSum = 0;
        let lenXSum = 0;
        let lenYSum = 0;

        for (let i = 0; i < x.length; i++) {
            const xVal = x[i];
            const yVal = y[i];

            // Dot product
            dotSum += xVal * yVal;
            // For magnitude of x
            lenXSum += xVal * xVal;
            // For magnitude of y
            lenYSum += yVal * yVal;
        }

        // Cosine Similarity of X, Y
        //  Sum(X * Y) / |X| * |Y|
        return dotSum / (Math.sqrt(lenXSum) * Math.sqrt(lenYSum));
    }

    /**
     * Extension method for vector division.
     * @param span The data vector
     * @param divisor The value to divide by.
     */
    public static divideByInPlace(span: number[], divisor: number): void {
        for (let i = 0; i < span.length; i++) {
            span[i] = span[i] / divisor;
        }
    }

    /**
     * Calculate the dot products of two vectors of type.
     *
     * @param x The first vector.
     * @param y The second vector.
     * @returns The dot product as a number.
     */
    public static dotProduct(x: number[] | ReadonlyArray<number>, y: number[] | ReadonlyArray<number>): number {
        if (x.length !== y.length) {
            throw new Error('Array lengths must be equal');
        }

        let dotSum = 0;
        for (let i = 0; i < x.length; i++) {
            dotSum += x[i] * y[i];
        }

        return dotSum;
    }

    /**
     * Calculate the Euclidean length of a vector of type.
     * @template TNumber The unmanaged data type (float, double currently supported).
     * @param {ReadonlyArray<TNumber>} x The vector.
     * @returns {number} Euclidean length as a double.
     */
    public static euclideanLength(x: number[] | ReadonlyArray<number>): number {
        return Math.sqrt(VectorOperations.dotProduct(x, x));
    }

    /**
     * Extension method to multiply a vector by a scalar.
     * @param vector The input vector.
     * @param multiplier The scalar.
     */
    public static multiplyByInPlace(vector: number[], multiplier: number): void {
        for (let i = 0; i < vector.length; i++) {
            vector[i] = vector[i] * multiplier;
        }
    }

    /**
     * Extension method to normalize a vector.
     *
     * @see https://en.wikipedia.org/wiki/Unit_vector
     */
    public static normalizeInPlace(vector: number[]): void {
        const length = VectorOperations.euclideanLength(vector);
        for (let i = 0; i < vector.length; i++) {
            vector[i] /= length;
        }
    }
}
