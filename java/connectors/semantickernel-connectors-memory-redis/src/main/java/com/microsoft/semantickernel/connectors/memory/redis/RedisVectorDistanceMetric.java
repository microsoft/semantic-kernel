package com.microsoft.semantickernel.connectors.memory.redis;

/* <summary>
  Supported distance metrics are {L2, IP, COSINE}. The default value is "COSINE".
  <see href="https://redis.io/docs/interact/search-and-query/search/vectors/"/>
 </summary> */
public class RedisVectorDistanceMetric {

    /* <summary> Euclidean distance between two vectors </summary> */
    public static final String L2 = "L2";

    /* <summary> Inner product of two vectors </summary> */
    public static final String IP = "IP";

    /* <summary> Cosine distance of two vectors </summary> */
    public static final String COS = "COSINE";
}
