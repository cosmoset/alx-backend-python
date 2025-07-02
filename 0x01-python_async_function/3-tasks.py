#!/usr/bin/env python3

'''
Module to create a task that calls the wait_random coroutine.
'''

import asyncio
wait_random = __import__("0-basic_async_syntax").wait_random


def task_wait_random(max_delay: int) -> asyncio.Task:
    '''
    This function creates and returns an asyncio.Task that calls the
    wait_random coroutine with the specified max_delay.

    Args:
        max_delay (int): Maximum delay for the wait_random coroutine.

    Returns:
        asyncio.Task: The asyncio.Task object.
    '''
    return asyncio.create_task(wait_random(max_delay))
