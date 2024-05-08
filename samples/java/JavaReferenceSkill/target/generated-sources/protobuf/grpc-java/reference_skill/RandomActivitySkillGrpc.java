package reference_skill;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 * <pre>
 * RandomActivitySkill is a service that provides methods related to random activities.
 * </pre>
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.54.0)",
    comments = "Source: activity.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class RandomActivitySkillGrpc {

  private RandomActivitySkillGrpc() {}

  public static final String SERVICE_NAME = "reference_skill.RandomActivitySkill";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<reference_skill.ActivityOuterClass.GetRandomActivityRequest,
      reference_skill.ActivityOuterClass.GetRandomActivityResponse> getGetRandomActivityMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetRandomActivity",
      requestType = reference_skill.ActivityOuterClass.GetRandomActivityRequest.class,
      responseType = reference_skill.ActivityOuterClass.GetRandomActivityResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<reference_skill.ActivityOuterClass.GetRandomActivityRequest,
      reference_skill.ActivityOuterClass.GetRandomActivityResponse> getGetRandomActivityMethod() {
    io.grpc.MethodDescriptor<reference_skill.ActivityOuterClass.GetRandomActivityRequest, reference_skill.ActivityOuterClass.GetRandomActivityResponse> getGetRandomActivityMethod;
    if ((getGetRandomActivityMethod = RandomActivitySkillGrpc.getGetRandomActivityMethod) == null) {
      synchronized (RandomActivitySkillGrpc.class) {
        if ((getGetRandomActivityMethod = RandomActivitySkillGrpc.getGetRandomActivityMethod) == null) {
          RandomActivitySkillGrpc.getGetRandomActivityMethod = getGetRandomActivityMethod =
              io.grpc.MethodDescriptor.<reference_skill.ActivityOuterClass.GetRandomActivityRequest, reference_skill.ActivityOuterClass.GetRandomActivityResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetRandomActivity"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  reference_skill.ActivityOuterClass.GetRandomActivityRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  reference_skill.ActivityOuterClass.GetRandomActivityResponse.getDefaultInstance()))
              .setSchemaDescriptor(new RandomActivitySkillMethodDescriptorSupplier("GetRandomActivity"))
              .build();
        }
      }
    }
    return getGetRandomActivityMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static RandomActivitySkillStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<RandomActivitySkillStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<RandomActivitySkillStub>() {
        @java.lang.Override
        public RandomActivitySkillStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new RandomActivitySkillStub(channel, callOptions);
        }
      };
    return RandomActivitySkillStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static RandomActivitySkillBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<RandomActivitySkillBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<RandomActivitySkillBlockingStub>() {
        @java.lang.Override
        public RandomActivitySkillBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new RandomActivitySkillBlockingStub(channel, callOptions);
        }
      };
    return RandomActivitySkillBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static RandomActivitySkillFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<RandomActivitySkillFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<RandomActivitySkillFutureStub>() {
        @java.lang.Override
        public RandomActivitySkillFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new RandomActivitySkillFutureStub(channel, callOptions);
        }
      };
    return RandomActivitySkillFutureStub.newStub(factory, channel);
  }

  /**
   * <pre>
   * RandomActivitySkill is a service that provides methods related to random activities.
   * </pre>
   */
  public interface AsyncService {

    /**
     * <pre>
     * GetRandomActivity is an RPC method that retrieves a random activity from an API.
     * </pre>
     */
    default void getRandomActivity(reference_skill.ActivityOuterClass.GetRandomActivityRequest request,
        io.grpc.stub.StreamObserver<reference_skill.ActivityOuterClass.GetRandomActivityResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetRandomActivityMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service RandomActivitySkill.
   * <pre>
   * RandomActivitySkill is a service that provides methods related to random activities.
   * </pre>
   */
  public static abstract class RandomActivitySkillImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return RandomActivitySkillGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service RandomActivitySkill.
   * <pre>
   * RandomActivitySkill is a service that provides methods related to random activities.
   * </pre>
   */
  public static final class RandomActivitySkillStub
      extends io.grpc.stub.AbstractAsyncStub<RandomActivitySkillStub> {
    private RandomActivitySkillStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected RandomActivitySkillStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new RandomActivitySkillStub(channel, callOptions);
    }

    /**
     * <pre>
     * GetRandomActivity is an RPC method that retrieves a random activity from an API.
     * </pre>
     */
    public void getRandomActivity(reference_skill.ActivityOuterClass.GetRandomActivityRequest request,
        io.grpc.stub.StreamObserver<reference_skill.ActivityOuterClass.GetRandomActivityResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetRandomActivityMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service RandomActivitySkill.
   * <pre>
   * RandomActivitySkill is a service that provides methods related to random activities.
   * </pre>
   */
  public static final class RandomActivitySkillBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<RandomActivitySkillBlockingStub> {
    private RandomActivitySkillBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected RandomActivitySkillBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new RandomActivitySkillBlockingStub(channel, callOptions);
    }

    /**
     * <pre>
     * GetRandomActivity is an RPC method that retrieves a random activity from an API.
     * </pre>
     */
    public reference_skill.ActivityOuterClass.GetRandomActivityResponse getRandomActivity(reference_skill.ActivityOuterClass.GetRandomActivityRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetRandomActivityMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service RandomActivitySkill.
   * <pre>
   * RandomActivitySkill is a service that provides methods related to random activities.
   * </pre>
   */
  public static final class RandomActivitySkillFutureStub
      extends io.grpc.stub.AbstractFutureStub<RandomActivitySkillFutureStub> {
    private RandomActivitySkillFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected RandomActivitySkillFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new RandomActivitySkillFutureStub(channel, callOptions);
    }

    /**
     * <pre>
     * GetRandomActivity is an RPC method that retrieves a random activity from an API.
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<reference_skill.ActivityOuterClass.GetRandomActivityResponse> getRandomActivity(
        reference_skill.ActivityOuterClass.GetRandomActivityRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetRandomActivityMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_GET_RANDOM_ACTIVITY = 0;

  private static final class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final AsyncService serviceImpl;
    private final int methodId;

    MethodHandlers(AsyncService serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_GET_RANDOM_ACTIVITY:
          serviceImpl.getRandomActivity((reference_skill.ActivityOuterClass.GetRandomActivityRequest) request,
              (io.grpc.stub.StreamObserver<reference_skill.ActivityOuterClass.GetRandomActivityResponse>) responseObserver);
          break;
        default:
          throw new AssertionError();
      }
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public io.grpc.stub.StreamObserver<Req> invoke(
        io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        default:
          throw new AssertionError();
      }
    }
  }

  public static final io.grpc.ServerServiceDefinition bindService(AsyncService service) {
    return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
        .addMethod(
          getGetRandomActivityMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              reference_skill.ActivityOuterClass.GetRandomActivityRequest,
              reference_skill.ActivityOuterClass.GetRandomActivityResponse>(
                service, METHODID_GET_RANDOM_ACTIVITY)))
        .build();
  }

  private static abstract class RandomActivitySkillBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    RandomActivitySkillBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return reference_skill.ActivityOuterClass.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("RandomActivitySkill");
    }
  }

  private static final class RandomActivitySkillFileDescriptorSupplier
      extends RandomActivitySkillBaseDescriptorSupplier {
    RandomActivitySkillFileDescriptorSupplier() {}
  }

  private static final class RandomActivitySkillMethodDescriptorSupplier
      extends RandomActivitySkillBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final String methodName;

    RandomActivitySkillMethodDescriptorSupplier(String methodName) {
      this.methodName = methodName;
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.MethodDescriptor getMethodDescriptor() {
      return getServiceDescriptor().findMethodByName(methodName);
    }
  }

  private static volatile io.grpc.ServiceDescriptor serviceDescriptor;

  public static io.grpc.ServiceDescriptor getServiceDescriptor() {
    io.grpc.ServiceDescriptor result = serviceDescriptor;
    if (result == null) {
      synchronized (RandomActivitySkillGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new RandomActivitySkillFileDescriptorSupplier())
              .addMethod(getGetRandomActivityMethod())
              .build();
        }
      }
    }
    return result;
  }
}
