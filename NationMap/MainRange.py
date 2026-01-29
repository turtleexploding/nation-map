import GetHomeBlocks # type: ignore
import DrawRange
import time

async def main(nation, zoom, line_thickness):
    
    start_time = time.time()

    result = GetHomeBlocks.fetch_all_homeblocks(nation)

    im = await DrawRange.draw(result, nation, zoom, line_thickness)

    print(f"{time.time() - start_time} seconds")

    return im
    
#if __name__ == "__main__":
#    asyncio.run(main())