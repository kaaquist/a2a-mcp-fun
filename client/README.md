# Client
### Run the client
Be aware that you need to start the wrapper before this here will work.  

To run the client: 
```text
uv run --env-file .env client --agent=http://localhost:8001
```
In the .env file I have added a OpenAI key. 
When running the Agent Supervisor I did not manage to get a local Ollama model to work. Therefor I use the OpenAI for the Supervisor.


### Start the A2A wrapper
Since I did not find a A2A Wrapper that would let me connect a A2A agent with a langgraph supervisor flow.  
I have created a MCP Tool with a A2A Client that connect to the A2A Server for weather.  
It seems quite cumbersome and a strange approach to get this here working.

So to get the full setup to work. Please start the `a2a_agent_mcp_tool.py` like so:
```text
uv run src/client/a2a_agent_mcp_tool.py
```
The endpoint for the A2A server is hardcoded in the file, so if you change the docker-compose setup to use a different port then you need to change it in here too.
another thing that is 

### create the `.env` file
```text
cat .env
OPENAI_API_KEY=sk-.... 
```

TODO's 
- [ ] Find a Ollama - small model the will work with the langgraph supervisor setup
- [ ] make the wrapper and client use arguments from commandline on startup to avoid hardcoded values.
- [ ] there is probably missing something

