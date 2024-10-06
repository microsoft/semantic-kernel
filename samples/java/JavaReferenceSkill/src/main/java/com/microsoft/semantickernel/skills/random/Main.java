package com.microsoft.semantickernel.skills.random;

import java.util.logging.Logger;

import io.grpc.Server;
import io.grpc.ServerBuilder;

import io.grpc.Server;
import io.grpc.ServerBuilder;

public class Main {

    private static final int PORT = 50051;

    public static void main(String[] args) {
        Logger logger =  java.util.logging.Logger.getLogger(Main.class.getName());

        Server server = ServerBuilder.forPort(PORT)
                .// The `addService` method in the code snippet is used to add a gRPC service
                // implementation to the server. In this case, it is adding an instance of the
                // `RandomActivitySkill` class as a service to the gRPC server being built. This
                // allows the server to handle requests related to the functionality provided by the
                // `RandomActivitySkill` class.
                addService(new RandomActivitySkill()).build();
                .addService(new RandomActivitySkill()).build();

        System.out.println("Starting server...");
        try {
            server.start();
            System.out.println("gRPC Server for random activity started on port " + PORT);
            server.awaitTermination();
        } catch (Exception e) {
            logger.severe("Error with request: " + e.getMessage());
            throw new RuntimeException(e);
        }
    }
}