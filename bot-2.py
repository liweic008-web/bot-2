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
        
        # 如果不是以 # 開頭，或者這條訊息是機器人自己發的，就直接跳過
        if not content.startswith("#") or message.author == bot.user:
            continue

        # 3. 檢查任務是否已完成 (檢查貼圖和回覆)
        is_completed = False

        # (A) 檢查有沒有人按愛心或大拇指
        for reaction in message.reactions:
            if str(reaction.emoji) in ["❤️", "👍"]:
                is_completed = True
                break

        # (B) 檢查這條訊息有沒有被「回覆」且寫著「已完成」
        if message.reference and message.reference.message_id:
            try:
                # 撈取被回覆的那一條訊息
                replied_msg = await channel.fetch_message(message.reference.message_id)
                if "已完成" in replied_msg.content:
                    is_completed = True
            except Exception:
                pass  # 如果訊息被刪除了就忽略

        # 如果被標記為完成了，我們就放過它，檢查下一條
        if is_completed:
            continue

        # 4. 用 Python 字串魔法，計算井字號數量並分類
        if content.startswith("###"):
            task_text = content.replace("###", "").strip()
            high_priority.append(f"🔴 {task_text} (由 {message.author.display_name} 建立)")
        elif content.startswith("##"):
            task_text = content.replace("##", "").strip()
            medium_priority.append(f"🟡 {task_text} (由 {message.author.display_name} 建立)")
        elif content.startswith("#"):
            task_text = content.replace("#", "").strip()
            low_priority.append(f"🔵 {task_text} (由 {message.author.display_name} 建立)")

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
