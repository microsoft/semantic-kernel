package com.microsoft.semantickernel.skills.random;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.CompletableFuture;

import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.mockito.Mockito;

import io.grpc.stub.StreamObserver;
import io.grpc.testing.GrpcServerRule;

import reference_skill.ActivityOuterClass.GetRandomActivityRequest;


import reference_skill.ActivityOuterClass.GetRandomActivityResponse;

// import reference_skill.RandomActivitySkillGrpc.RandomActivitySkillBlockingStub; // Remove the unused import statement

public class RandomActivitySkillTest {

    @Rule
    public GrpcServerRule grpcServerRule = new GrpcServerRule().directExecutor();

    // Remove the unused field declaration

    @Before
    public void setUp() {
        grpcServerRule.getServiceRegistry().addService(new RandomActivitySkill());
    }

    @Test
    public void testGetRandomActivity() throws Exception {
        HttpClient httpClient = mock(HttpClient.class);
        HttpResponse<String> httpResponse = mock(HttpResponse.class, Mockito.withSettings().defaultAnswer(Mockito.RETURNS_DEEP_STUBS));
        CompletableFuture<HttpResponse<String>> responseFuture = CompletableFuture.completedFuture(httpResponse);

        extracted(httpClient, responseFuture);
        when(httpResponse.body()).thenReturn("{\"activity\":\"Test Activity\"}");

        RandomActivitySkill randomActivitySkill = new RandomActivitySkill() {
        };
        
        GetRandomActivityRequest request = GetRandomActivityRequest.newBuilder().build();
        GetRandomActivityRequest getRandomActivityRequest = GetRandomActivityRequest.newBuilder().build();
        StreamObserver<GetRandomActivityResponse> responseObserver = mock(StreamObserver.class);
        randomActivitySkill.getRandomActivity(request, responseObserver);

        verify(responseObserver).onNext(any(GetRandomActivityResponse.class));
        verify(responseObserver).onCompleted();
    }

    private void extracted(HttpClient httpClient, CompletableFuture<HttpResponse<String>> responseFuture) {
        HttpClient mockHttpClient = mock(HttpClient.class);
        CompletableFuture<HttpResponse<String>> mockResponseFuture = CompletableFuture.<HttpResponse<String>>completedFuture(mock(HttpResponse.class));
    
        // Use type parameters explicitly
        when(mockHttpClient.sendAsync(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn((CompletableFuture<HttpResponse<String>>) mockResponseFuture);
    
        // Your test logic here
    }
}
