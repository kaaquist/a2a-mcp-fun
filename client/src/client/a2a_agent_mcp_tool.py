import asyncio
import base64
import os
import urllib
import logging

from uuid import uuid4

import asyncclick as click

from google_a2a.common.client import A2ACardResolver, A2AClient
from google_a2a.common.types import TaskState
from google_a2a.common.utils.push_notification_auth import PushNotificationReceiverAuth
from mcp.server.fastmcp import FastMCP


"""
This here is a modified version of the cli.py file that is found here: https://github.com/google/A2A/tree/main/samples/python/hosts/cli
Everything has been cut from the original client to get a "barebone" minimal client.
Then it has been transformed into a FastMCP tool - to make it compatible with Langchain - hence as of coding there are no langchain to a2a connector.

"""

mcp = FastMCP("weather", host="localhost", port=8090)
logger = logging.getLogger(__name__)


@mcp.tool()
async def get_weather(location_prompt: str, transaction_id: str) -> str:
    """Get the city and the country and return the weather forcast for a week"""
    card_resolver = A2ACardResolver("http://localhost:8001")
    card = card_resolver.get_agent_card()

    logger.debug('======= Agent Card ========')
    logger.debug(card.model_dump_json(exclude_none=True))

    client = A2AClient(agent_card=card)
    session_id = uuid4().hex

    streaming = card.capabilities.streaming
    message = {
        'role': 'user',
        'parts': [
            {
                'type': 'text',
                'text': location_prompt,
            }
        ],
    }


    payload = {
        'id': transaction_id,
        'sessionId': session_id,
        'acceptedOutputModes': ['text'],
        'message': message,
    }

    task_result = None
    if streaming:
        response_stream = client.send_task_streaming(payload)
        async for result in response_stream:
            logger.debug(
                f'stream event => {result.model_dump_json(exclude_none=True)}'
            )
        task_result = await client.get_task({'id': transaction_id})
    else:
        task_result = await client.send_task(payload)
        logger.debug(f'\n{task_result.model_dump_json(exclude_none=True)}')
    return task_result.model_dump_json(exclude_none=True)


if __name__ == '__main__':
    try:
        mcp.run(transport="sse")
    except KeyboardInterrupt as kie:
        pass