package com.microsoft.semantickernel.skills.random;

import io.grpc.stub.StreamObserver;
import io.grpc.testing.GrpcServerRule;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import reference_skill.ActivityOuterClass;
import reference_skill.RandomActivitySkillGrpc;

import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.CompletableFuture;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

public class RandomActivitySkillTest {

    @Rule
    public GrpcServerRule grpcServerRule = new GrpcServerRule().directExecutor();

    private RandomActivitySkillGrpc.RandomActivitySkillBlockingStub blockingStub;

    @Before
    public void setUp() {
        grpcServerRule.getServiceRegistry().addService(new RandomActivitySkill());
        blockingStub = RandomActivitySkillGrpc.newBlockingStub(grpcServerRule.getChannel());
    }

    @Test
    public void testGetRandomActivity() throws Exception {
        HttpClient httpClient = mock(HttpClient.class);
        HttpResponse<String> httpResponse = mock(HttpResponse.class);
        CompletableFuture<HttpResponse<String>> responseFuture = CompletableFuture.completedFuture(httpResponse);

        when(httpClient.sendAsync(any(HttpRequest.class), any(HttpResponse.BodyHandler.class))).thenReturn(responseFuture);
        when(httpResponse.body()).thenReturn("{\"activity\":\"Test Activity\"}");

        RandomActivitySkill randomActivitySkill = new RandomActivitySkill() {
        };

        ActivityOuterClass.GetRandomActivityRequest request = ActivityOuterClass.GetRandomActivityRequest.newBuilder().build();
        StreamObserver<ActivityOuterClass.GetRandomActivityResponse> responseObserver = mock(StreamObserver.class);
        randomActivitySkill.getRandomActivity(request, responseObserver);

        verify(responseObserver).onNext(any(ActivityOuterClass.GetRandomActivityResponse.class));
        verify(responseObserver).onCompleted();
    }
}
