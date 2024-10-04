package com.microsoft.semantickernel.skills.random;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
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

import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Rule;
import org.junit.Test;
import org.mockito.Mockito;

import io.grpc.stub.StreamObserver;
import io.grpc.testing.GrpcServerRule;
import reference_skill.ActivityOuterClass.GetRandomActivityRequest;
import reference_skill.ActivityOuterClass.GetRandomActivityResponse;

// import reference_skill.RandomActivitySkillGrpc.RandomActivitySkillBlockingStub; // Remove the unused import statement
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

public class RandomActivitySkillTest {

    @Rule
    public GrpcServerRule grpcServerRule = new GrpcServerRule().directExecutor();

    // Remove the unused field declaration
    private RandomActivitySkillGrpc.RandomActivitySkillBlockingStub blockingStub;

    @Before
    public void setUp() {
        grpcServerRule.getServiceRegistry().addService(new RandomActivitySkill());
    }

    /**
     * @throws Exception
     */
    @Test
    public void testGetRandomActivity() throws Exception {
        HttpClient httpClient = mock(HttpClient.class);
        HttpResponse<String> httpResponse = mock(HttpResponse.class, Mockito.withSettings().defaultAnswer(Mockito.RETURNS_DEEP_STUBS));
        CompletableFuture<HttpResponse<String>> responseFuture = CompletableFuture.completedFuture(httpResponse);

        extracted(httpClient, responseFuture);
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
        
        GetRandomActivityRequest request = GetRandomActivityRequest.newBuilder().build();
        GetRandomActivityRequest getRandomActivityRequest = GetRandomActivityRequest.newBuilder().build();
        StreamObserver<GetRandomActivityResponse> responseObserver = mock(StreamObserver.class);
        randomActivitySkill.getRandomActivity(request, responseObserver);

        verify(responseObserver).onNext(any(GetRandomActivityResponse.class));
        verify(responseObserver).onCompleted();
    }

    @Test
    public void testName() {
        
    }

    @BeforeClass
    public static void beforeClass() {
        
    }

    @Before
    public void setUp2() {
        
    }

    @After
    public void tearDown() {
        
    }

    @AfterClass
    public static void afterClass() {
        
    }

    private void extracted(HttpClient httpClient, CompletableFuture<HttpResponse<String>> responseFuture) {
        HttpClient mockHttpClient = mock(HttpClient.class);
        CompletableFuture<HttpResponse<String>> mockResponseFuture = CompletableFuture.<HttpResponse<String>>completedFuture(mock(HttpResponse.class));
    
        // Use type parameters explicitly
        @SuppressWarnings("unchecked")
        when(mockHttpClient.<HttpResponse<String>>sendAsync(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(mockResponseFuture);
    
        // Your test logic here
    }

        ActivityOuterClass.GetRandomActivityRequest request = ActivityOuterClass.GetRandomActivityRequest.newBuilder().build();
        StreamObserver<ActivityOuterClass.GetRandomActivityResponse> responseObserver = mock(StreamObserver.class);
        randomActivitySkill.getRandomActivity(request, responseObserver);

        verify(responseObserver).onNext(any(ActivityOuterClass.GetRandomActivityResponse.class));
        verify(responseObserver).onCompleted();
    }
}
