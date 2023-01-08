from async_request import *
import asyncio
from datetime import datetime, time



if __name__ == '__main__':
    start = datetime.now()
    asyncio.run(main_func())
    print("Время загрузки:", datetime.now()-start)

