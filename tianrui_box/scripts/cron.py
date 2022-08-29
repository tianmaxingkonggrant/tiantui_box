


import time
from sanic import Sanic
from sanic.response import json
app = Sanic("AppName")
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
def cron_job():
    print('打印当前时间:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

@app.route('/')
async def index(request):
    # generate a URL for the endpoint `post_handler`
    print("浏览器里打开一下首页")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(cron_job, CronTrigger(day="*", hour="*",
                 minute="*", second="*/2"))
    scheduler.start()
    return json({"hello": "thank you"})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
