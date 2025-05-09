import sys
def my_except_hook(exctype, value, traceback):
  if exctype == KeyboardInterrupt:
    Log.error("main global error handler", exc_info=(exctype, value, traceback))
  else:
    sys.__excepthook__(exctype, value, traceback)
sys.excepthook = my_except_hook

from init import appconfig
import fastapi
import uvicorn
from job import WARAEventLoop, WARAApiGenScheduledJob, WARAHistoryCleanUpScheduledJob
from wara.wara_api import WARAApi
from memory_queue import MemoryQueue
from routers import health, wara, networkmap
import log as Log


# init global queue
wara_report_gen_queue = MemoryQueue()

app = fastapi.FastAPI()

app.include_router(health.router)
app.include_router(wara.router)
app.include_router(networkmap.router)

_waraapi = WARAApi(config=appconfig)




# run background jobs
if appconfig.enable_wara:
    Log.debug('main - WARA is enabled')
    WARAEventLoop().start()
    WARAApiGenScheduledJob().init_wara_report_gen_scheduled_job()
    WARAHistoryCleanUpScheduledJob().init_clean_history_scheduled_job()

    # execute wara 1 time upon startup
    wara_report_gen_queue.enqueue('run_wara')
else:
    Log.debug('main - WARA is disabled')


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)