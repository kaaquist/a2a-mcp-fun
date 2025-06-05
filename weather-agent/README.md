# Weather Agent

### The A2A wrapper to LangGraph
Since I did not find a A2A Wrapper that would let me connect a A2A agent with a langgraph supervisor/agent flow.  
I have created a MCP Tool with a A2A Client that connect to the A2A Server in this here case the weather a2a agent.  
It seems quite cumbersome and a strange approach to get this here working but that is how it is.

The `a2a_agent_mcp_tool.py` is part of the `docker-compose` setup - but if needed one can start it like so, locally:
```text
uv run src/client/a2a_agent_mcp_tool.py
```
The endpoint for the A2A client/server is hardcoded in the file, so if you need to run it locally or change the docker-compose setup to use a different port then you need to change it in here too. 
another thing that is.

_**Be aware**_ that the timeout for the A2A Client in the Google A2A lib is changed in the Dockerfile for the tool.
This is done to avoid timeout errors. From `dockerfile.a2a-agent-tool`:
```text
...
# We change the a2a client time out in the package. As of writing this is not an argument to the client - therefore this here hack
RUN sed "s/timeout=30/timeout=120/" /opt/.venv/lib/python3.13/site-packages/google_a2a/common/client/client.py > client.py && \
    rm -v /opt/.venv/lib/python3.13/site-packages/google_a2a/common/client/client.py && \
    mv -v client.py /opt/.venv/lib/python3.13/site-packages/google_a2a/common/client/client.py
...
```