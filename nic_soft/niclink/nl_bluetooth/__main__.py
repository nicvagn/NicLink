import nl_bluetooth
import asyncio
import readchar
async def run(): 
    await nl_bluetooth.connect()
    while True:
        print(nl_bluetooth.getFEN())

async def main():
    await run()
    readchar.readkey()

main()
