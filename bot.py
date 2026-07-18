import os
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import re

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
# ─── 💡 頻道 ID 寫死大絕招 ───
CHANNEL_ID = 1527992244043255899  # 👈 請記得換成你真正的 Discord 頻道 ID 喔！

@bot.event
async def on_ready():
    print(f"【系統通知】機器人 {bot.user} 已上線。")
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("【錯誤】找不到指定的頻道，請檢查 CHANNEL_ID 是否正確。")
        await bot.close()
        return

    # ─── ✨ 核心修正：一上線就強制把 now 定義為真正的台灣時間！ ───
    now = datetime.utcnow() + timedelta(hours=8)
    print(f"【現在時間】台灣時間：{now.strftime('%Y-%m-%d %H:%M')}")

    high_priority = []
    medium_priority = []
    low_priority = []

    # 1. 撈取歷史訊息
    async for message in channel.history(limit=100):
        content = message.content.strip()
        
        # 沒用井字號開頭，或是機器人自己發的，就跳過
        if not content.startswith("#") or message.author == bot.user:
            continue

        # 檢查是否已完成 (按讚或回覆已完成)
        is_completed = False
        for reaction in message.reactions:
            if str(reaction.emoji) in ["❤️", "👍"]:
                is_completed = True
                break
        if message.reference and message.reference.message_id:
            try:
                replied_msg = await channel.fetch_message(message.reference.message_id)
                if "已完成" in replied_msg.content:
                    is_completed = True
            except Exception:
                pass
        if is_completed:
            continue

        # ─── ✨ 預設時間提示文字 ───
        time_hint = ""  
        
        # ────── 🧭 日期與時間雙重辨認魔法 ──────
        datetime_match = re.search(r"(?:(\d{1,2})[/\-](\d{1,2})\s+)?(\d{1,2}):(\d{2})", content)
        if datetime_match:
            month_str = datetime_match.group(1)
            day_str = datetime_match.group(2)
            hour = int(datetime_match.group(3))
            minute = int(datetime_match.group(4))
            
            task_year = now.year
            task_month = int(month_str) if month_str else now.month
            task_day = int(day_str) if day_str else now.day
            
            try:
                task_time = datetime(task_year, task_month, task_day, hour, minute, 0, 0)
                
                if task_time <= now:
                    # 已經超時了！
                    diff = now - task_time
                    days = diff.days
                    hours = diff.seconds // 3600
                    minutes = (diff.seconds % 3600) // 60
                    if days > 0:
                        over_str = f"{days}天{hours}小時"
                    elif hours > 0:
                        over_str = f"{hours}小時{minutes}分鐘"
                    else:
                        over_str = f"{minutes}分鐘"
                    time_hint = f" ⏰ **[已超時 {over_str}！]**"
                else:
                    # 還沒到期，計算剩餘時間！
                    diff = task_time - now
                    days = diff.days
                    hours = diff.seconds // 3600
                    minutes = (diff.seconds % 3600) // 60
                    if days > 0:
                        remain_str = f"{days}天{hours}小時"
                    elif hours > 0:
                        remain_str = f"{hours}小時{minutes}分鐘"
                    else:
                        remain_str = f"{minutes}分鐘"
                    time_hint = f" ⏳ (剩餘 {remain_str})"
            except ValueError:
                pass
        # ───────────────────────────────────────────────────

        # ────── 🎯 反轉排版：換上超生動的任務前置顏文字 ──────
        msg_tw_time = message.created_at + timedelta(hours=8)
        time_created_str = msg_tw_time.strftime('%m/%d %H:%M')
        
        if content.startswith("###"):
            task_text = content.replace("###", "").strip()
            low_priority.append(f" (☕•ㅂ•) ### {task_text}{time_hint} (由 {message.author.display_name} 建立於 {time_created_str})")
        elif content.startswith("##"):
            task_text = content.replace("##", "").strip()
            medium_priority.append(f" (⌛'ω') ## {task_text}{time_hint} (由 {message.author.display_name} 建立於 {time_created_str})")
        elif content.startswith("#"):
            task_text = content.replace("#", "").strip()
            high_priority.append(f" (🚨ﾟДﾟ) # {task_text}{time_hint} (由 {message.author.display_name} 建立於 {time_created_str})")
        # ───────────────────────────────────────────────────

    # ─── 🚨 總結輸出區塊 (前面保留 4 個空格) ───
    report_time_str = now.strftime('%Y/%m/%d %H:%M')
    
    report = f"📋 **【今日未完成待辦清單總結】** (發布時間：{report_time_str})\n"
    report += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    report += " (🚨ﾟДﾟ)b **「進度告急！火燒屁股重要任務」**\n" + ("\n".join(high_priority) if high_priority else "  (๑´ㅂ`๑) _目前沒有任何緊急任務，讚啦！_") + "\n\n"
    report += " (⌛'ω')p **「記得要做！中等難度任務」**\n" + ("\n".join(medium_priority) if medium_priority else "  _暫無任務_") + "\n\n"
    report += " (☕•ㅂ•)旦 **「慢慢來！一般輕鬆任務」**\n" + ("\n".join(low_priority) if low_priority else "  _暫無任務_") + "\n"
    
    # 發送報告並關機
    await channel.send(report)
    await bot.close()
