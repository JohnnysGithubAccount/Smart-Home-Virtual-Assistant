import json
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta


class ToolScheduler:
    def __init__(self, tool_executor):
        """
        tool_executor: a callable that actually runs the tool
                       e.g. execute_tool(tool_name, args)
        """
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.tool_executor = tool_executor

    def add_schedule(self, schedule_json: str):
        """Parse schedule JSON and register job"""
        schedule = json.loads(schedule_json)

        tool_name = schedule["tool"]
        args = schedule["args"]
        time = schedule["time"]
        repeat = schedule.get("repeat", "once")
        duration = schedule.get("duration")
        end_time = schedule.get("end_time")

        # Build trigger
        if repeat == "once":
            trigger = DateTrigger(run_date=self._parse_time(time))
        elif repeat == "periodic":
            seconds = self._parse_interval(time)
            trigger = IntervalTrigger(seconds=seconds)
        elif repeat == "daily":
            hour, minute = map(int, time.split(":"))
            trigger = CronTrigger(hour=hour, minute=minute)
        elif repeat == "weekly":
            weekday, hm = time.split(" ")
            hour, minute = map(int, hm.split(":"))
            trigger = CronTrigger(day_of_week=weekday, hour=hour, minute=minute)
        else:
            raise ValueError(f"Unknown repeat: {repeat}")

        # Schedule job
        self.scheduler.add_job(
            self.tool_executor,
            trigger,
            args=[tool_name, args],
            id=f"{tool_name}_{datetime.now().timestamp()}",
            end_date=self._parse_time(end_time) if end_time else None
        )

    def _parse_time(self, t: str):
        """Parse time strings into datetime"""
        if not t:
            return None
        if "T" in t:  # ISO datetime
            return datetime.fromisoformat(t)
        elif ":" in t:  # clock time today or tomorrow
            hour, minute = map(int, t.split(":"))
            now = datetime.now()
            candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate < now:
                candidate += timedelta(days=1)
            return candidate
        elif t.startswith("after "):  # e.g., "after 1h"
            num, unit = t.split()[1:]
            num = int(num)
            if unit.startswith("h"):
                return datetime.now() + timedelta(hours=num)
            elif unit.startswith("m"):
                return datetime.now() + timedelta(minutes=num)
        return None

    def _parse_interval(self, t: str):
        """Convert 'every 30m' / 'every 1h' to seconds"""
        if "m" in t:
            return int(t.replace("every", "").replace("m", "").strip()) * 60
        if "h" in t:
            return int(t.replace("every", "").replace("h", "").strip()) * 3600
        return int(t)


# Example executor
def execute_tool(tool_name, args):
    print(f"[EXECUTE] Running {tool_name} with {args} at {datetime.now()}")

# Usage
async def main():
    scheduler = ToolScheduler(execute_tool)

    schedule_json = json.dumps({
        "scheduled": True,
        "tool": "control_lights",
        "args": {"room": "kitchen", "status": True},
        "time": "19:00",
        "repeat": "daily",
        "duration": "1h"
    })

    scheduler.add_schedule(schedule_json)

    await asyncio.sleep(int(60 * 5))  # keep alive for demo


if __name__ == "__main__":
    asyncio.run(main())
