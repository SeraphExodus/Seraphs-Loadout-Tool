#!/usr/bin/env python

import asyncio

from websockets.asyncio.server import serve

async def hello(websocket):
    number = await websocket.recv()
    print(f"<<< {number}")

    try:
        number = float(number)
        mathed = round(number * 1.07,1)
        output = f"Post-RE: {mathed}"
    except:
        output = f"Invalid Input: {number}"

    await websocket.send(output)
    print(f">>> {output}")

async def main():
    async with serve(hello, "localhost", 8765) as server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())