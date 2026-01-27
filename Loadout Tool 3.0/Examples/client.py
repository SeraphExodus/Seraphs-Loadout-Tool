#!/usr/bin/env python

from websockets.sync.client import connect

def hello():
    uri = "ws://localhost:8765"
    with connect(uri) as websocket:
        number = input("Give me a number. ")

        websocket.send(number)
        print(f">>> {number}")

        mathed = websocket.recv()
        print(f"<<< {mathed}")

if __name__ == "__main__":
    hello()