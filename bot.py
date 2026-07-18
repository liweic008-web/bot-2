import os
import discord
from discord.ext import commands

# 1. 初始化機器人
intents = discord.Intents.default()
intents.message_content = True  # 必須開啟，這樣機器人才看得到歷史訊息的「文字內容」
intents.reactions = True        # 必須開啟，這樣機器人才看得到「貼圖」

bot = commands.Bot(command_prefix="!", intents=intents)

# 讀取環境變數
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1527992244043255899

@bot.event
async def on_ready():
    print(f"【系統通知】機器人 {bot.user} 已成功上線，準備開始抓地主！")
    
    # 找到我們要檢查的 Discord 頻道
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("【錯誤】找不到指定的頻道，請檢查 CHANNEL_ID 是否正確。")
        await bot.close()
        return

    # 初始化三個難度的任務清單
    high_priority = []    ### 重要
    medium_priority = []  ## 中等
    low_priority = []     # 一般

    print("【進度】正在撈取過去的歷史訊息...")
    
    # 2. 開始撈取頻道最近的 100 條訊息
    async for message in channel.history(limit=100):
        content = message.content.strip()
        
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

        # ─── ✨ 關鍵修正：先把 time_hint 準備好，放最前面！ ───
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
                    display_time = task_time.strftime('%m/%d %H:%M') if month_str else datetime_match.group(0)
                    time_hint = f" ⏰ **[已超時 {over_str}！]**"
                else:
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

        # ────── 🎯 反轉排版：井字號越少，字體越大、越重要！ ──────
        # 這樣一來，下面的 time_hint 在使用時就絕對不會出錯了！
        if content.startswith("###"):
            task_text = content.replace("###", "").strip()
            low_priority.append(f"🔵 ### {task_text}{time_hint} (由 {message.author.display_name} 建立)")
        elif content.startswith("##"):
            task_text = content.replace("##", "").strip()
            medium_priority.append(f"🟡 ## {task_text}{time_hint} (由 {message.author.display_name} 建立)")
        elif content.startswith("#"):
            task_text = content.replace("#", "").strip()
            high_priority.append(f"🔴 # {task_text}{time_hint} (由 {message.author.display_name} 建立)")
        # ───────────────────────────────────────────────────
    # 5. 組裝成精美的待辦清單報告
    report = "📋 **【今日未完成待辦清單總結】**\n"
    report += "大家丟出來的任務幫你們整理好囉，完成的記得按 ❤️ 或回覆「已完成」！\n"
    report += "───────────────────\n\n"

    report += "**重要任務 (🔴)**\n"
    report += "\n".join(high_priority) if high_priority else "_暫無重要任務，太棒了！_"
    report += "\n\n"

    report += "**中等任務 (🟡)**\n"
    report += "\n".join(medium_priority) if medium_priority else "_暫無中等任務。_"
    report += "\n\n"

    report += "**一般任務 (🔵)**\n"
    report += "\n".join(low_priority) if low_priority else "_暫無一般任務。_"
    report += "\n\n"
    
    report += "───────────────────\n"
    report += "*本報告由 GitHub 每日自動化精靈產生*"

    # 6. 發送報告，並優雅地關機
    await channel.send(report)
    print("【系統通知】清單發送成功！正在關閉機器人以節省資源...")
    await bot.close()

# 啟動機器人
if TOKEN:
    bot.run(TOKEN)
else:
    print("【錯誤】找不到 DISCORD_TOKEN 環境變數。")
