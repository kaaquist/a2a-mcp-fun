import asyncio
import base64
import os
import urllib

from uuid import uuid4

import asyncclick as click

from google_a2a.common.client import A2ACardResolver, A2AClient
from google_a2a.common.types import TaskState
from google_a2a.common.utils.push_notification_auth import PushNotificationReceiverAuth

"""
This here is a modified version of the cli.py file that is found here: https://github.com/google/A2A/tree/main/samples/python/hosts/cli
Everything has been cut from the original client to get a "barebone" minimal client.
 
"""


@click.command()
@click.option('--agent', default='http://localhost:10000')
@click.option('--history', default=False)
async def cli(
    agent,
    history
):
    card_resolver = A2ACardResolver(agent)
    card = card_resolver.get_agent_card()

    print('======= Agent Card ========')
    print(card.model_dump_json(exclude_none=True))

    client = A2AClient(agent_card=card)
    session_id = uuid4().hex

    continue_loop = True
    streaming = card.capabilities.streaming

    while continue_loop:
        task_id = uuid4().hex
        print('=========  starting a new task ======== ')
        continue_loop = await completeTask(
            client,
            streaming,
            task_id,
            session_id,
        )

        if history and continue_loop:
            print('========= history ======== ')
            task_response = await client.get_task(
                {'id': task_id, 'historyLength': 10}
            )
            print(
                task_response.model_dump_json(
                    include={'result': {'history': True}}
                )
            )


async def completeTask(
    client: A2AClient,
    streaming,
    task_id,
    session_id,
):
    prompt = click.prompt(
        '\nWhat do you want to send to the agent? (:q or quit to exit)'
    )
    if prompt.strip() == ':q' or prompt.strip() == 'quit':
        return False

    message = {
        'role': 'user',
        'parts': [
            {
                'type': 'text',
                'text': prompt,
            }
        ],
    }

    file_paths = []
    while True:
        file_path = click.prompt(
            'Select a file path to attach (or press enter to finish adding files)',
            default='',
            show_default=False,
        )
        if not file_path or file_path.strip() == '':
            break
        file_paths.append(file_path.strip())

    for file_path in file_paths:
        try:
            with open(file_path, 'rb') as f:
                file_content = base64.b64encode(f.read()).decode('utf-8')
                file_name = os.path.basename(file_path)

            message['parts'].append(
                {
                    'type': 'file',
                    'file': {
                        'name': file_name,
                        'bytes': file_content,
                    },
                }
            )
            print(f'Attached file: {file_name}')
        except FileNotFoundError:
            print(f'Error: File not found at {file_path}. Skipping.')
        except Exception as e:
            print(f'Error reading file {file_path}: {e}. Skipping.')

    payload = {
        'id': task_id,
        'sessionId': session_id,
        'acceptedOutputModes': ['text'],
        'message': message,
    }

    task_result = None
    if streaming:
        response_stream = client.send_task_streaming(payload)
        async for result in response_stream:
            print(
                f'stream event => {result.model_dump_json(exclude_none=True)}'
            )
        task_result = await client.get_task({'id': task_id})
    else:
        task_result = await client.send_task(payload)
        print(f'\n{task_result.model_dump_json(exclude_none=True)}')

    ## if the result is that more input is required, loop again.
    state = TaskState(task_result.result.status.state)
    if state.name == TaskState.INPUT_REQUIRED.name:
        return await completeTask(
            client,
            streaming,
            task_id,
            session_id,
        )
    ## task is complete
    return True

def main():
    asyncio.run(cli())


if __name__ == '__main__':
    asyncio.run(cli())