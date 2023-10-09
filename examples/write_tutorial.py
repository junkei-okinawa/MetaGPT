#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/9/4 21:40:57
@Author  : Stitch-z
@File    : tutorial_assistant.py
"""
import asyncio

import fire
from metagpt.roles.tutorial_assistant import TutorialAssistant


async def write_tutorial(topic="Write a tutorial about MySQL", language="Japanese"):
    role = TutorialAssistant(language=language)
    await role.run(topic)

def main(topic="Write a tutorial about MySQL", language="Japanese"):
    asyncio.run(write_tutorial(topic, language))

if __name__ == '__main__':
    fire.Fire(main)

