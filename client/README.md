# Client
### Run the client
Be aware that you need to start the wrapper before this here will work.  

To run the client: 
```text
uv run --env-file .env client --agent=http://localhost:8001
```
In the .env file I have added a OpenAI key. 
When running the Agent Supervisor I did not manage to get a local Ollama model to work. Therefor I use the OpenAI for the Supervisor.


### create the `.env` file
```text
cat .env
OPENAI_API_KEY=sk-.... 
```

TODO's 
- [ ] Find a Ollama - small model the will work with the langgraph supervisor setup
- [ ] make the wrapper and client use arguments from commandline on startup to avoid hardcoded values.
- [ ] there is probably missing something

