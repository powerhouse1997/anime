# APScheduler setupfrom apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.news import post_latest_news
from services.shikimori import post_today_schedule

def setup_scheduler(bot, dispatcher):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(post_latest_news, "interval", hours=1, args=[bot])
    scheduler.add_job(post_today_schedule, "cron", hour=7, minute=0, args=[bot])
    scheduler.start()
