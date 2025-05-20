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
    sessionId = uuid4().hex

    continue_loop = True
    streaming = card.capabilities.streaming

    while continue_loop:
        taskId = uuid4().hex
        print('=========  starting a new task ======== ')
        continue_loop = await completeTask(
            client,
            streaming,
            taskId,
            sessionId,
        )

        if history and continue_loop:
            print('========= history ======== ')
            task_response = await client.get_task(
                {'id': taskId, 'historyLength': 10}
            )
            print(
                task_response.model_dump_json(
                    include={'result': {'history': True}}
                )
            )


async def completeTask(
    client: A2AClient,
    streaming,
    taskId,
    sessionId,
):
    prompt = click.prompt(
        '\nWhat do you want to send to the agent? (:q or quit to exit)'
    )
    if prompt == ':q' or prompt == 'quit':
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
        'id': taskId,
        'sessionId': sessionId,
        'acceptedOutputModes': ['text'],
        'message': message,
    }

    taskResult = None
    if streaming:
        response_stream = client.send_task_streaming(payload)
        async for result in response_stream:
            print(
                f'stream event => {result.model_dump_json(exclude_none=True)}'
            )
        taskResult = await client.get_task({'id': taskId})
    else:
        taskResult = await client.send_task(payload)
        print(f'\n{taskResult.model_dump_json(exclude_none=True)}')

    ## if the result is that more input is required, loop again.
    state = TaskState(taskResult.result.status.state)
    if state.name == TaskState.INPUT_REQUIRED.name:
        return await completeTask(
            client,
            streaming,
            taskId,
            sessionId,
        )
    ## task is complete
    return True

def main():
    asyncio.run(cli())


if __name__ == '__main__':
    asyncio.run(cli())