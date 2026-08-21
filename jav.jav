Tool helloTool = Tool.builder()
        .name("hello")
        .description("Returns a greeting")
        .inputSchema("""
                {
                  "type": "object",
                  "properties": {
                    "name": {
                      "type": "string"
                    }
                  },
                  "required": ["name"]
                }
                """)
        .build();