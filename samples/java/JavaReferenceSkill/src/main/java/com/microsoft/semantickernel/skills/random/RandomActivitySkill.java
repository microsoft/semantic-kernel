package com.microsoft.semantickernel.skills.random;

import io.grpc.stub.StreamObserver;
import reference_skill.ActivityOuterClass;
import reference_skill.RandomActivitySkillGrpc;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.CompletableFuture;
import java.util.logging.Logger;

public class RandomActivitySkill extends RandomActivitySkillGrpc.RandomActivitySkillImplBase {

    public static final String API_ACTIVITY_URL = "https://www.boredapi.com/api/activity";

    /**
     * <pre>
     * GetRandomActivity is an RPC method that retrieves a random activity from an API.
     * </pre>
     *
     * @param request
     * @param responseObserver
     */
    @Override
    public void getRandomActivity(ActivityOuterClass.GetRandomActivityRequest request, StreamObserver<ActivityOuterClass.GetRandomActivityResponse> responseObserver) {
        Logger logger =  java.util.logging.Logger.getLogger(this.getClass().getName());
        HttpClient httpClient = HttpClient.newHttpClient();
        HttpRequest httpRequest = HttpRequest.newBuilder()
                .uri(URI.create(API_ACTIVITY_URL))
                .build();
        try {
            CompletableFuture<HttpResponse<String>> response = httpClient.sendAsync(httpRequest, HttpResponse.BodyHandlers.ofString());
            logger.info("Response: " + response.get().body());
            responseObserver.onNext(ActivityOuterClass.GetRandomActivityResponse.newBuilder().setActivity(response.get().body()).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            logger.severe("Error with request: " + e.getMessage());
        }
    }
}
