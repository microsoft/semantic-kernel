package com.microsoft.semantickernel.skills.random;

import io.grpc.Server;
import io.grpc.ServerBuilder;

import java.util.logging.Logger;

public class Main {

    private static final int PORT = 50051;

    public static void main(String[] args) {
        Logger logger =  java.util.logging.Logger.getLogger(Main.class.getName());

        Server server = ServerBuilder.forPort(PORT)
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