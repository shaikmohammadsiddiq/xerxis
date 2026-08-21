McpSyncServer server =
        McpServer.sync(transportProvider)
                .serverInfo("java-mcp-server", "1.0.0")
                .capabilities(
                        McpSchema.ServerCapabilities.builder()
                                .tools(true)
                                .build()
                )
                .build();