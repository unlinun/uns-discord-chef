import os
import discord
from discord import app_commands
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 載入環境變數
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# 2. 設定 Gemini
genai.configure(api_key=GEMINI_KEY)
# 初始化模型 (使用 gemini-1.5-flash，速度快且免費額度充足)
model = genai.GenerativeModel('gemini-1.5-flash')

class ChefBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = ChefBot()

@bot.event
async def on_ready():
    print(f'✅ 機器人已上線：{bot.user}')

# 3. 定義指令 /cook
@bot.tree.command(name="cook", description="給食材，Gemini 大廚給您食譜")
@app_commands.describe(ingredients="例如：雞胸肉, 蔥, 蛋", style="中式、泰式...", method="炒、蒸...")
async def cook(interaction: discord.Interaction, ingredients: str, style: str = "不拘", method: str = "不拘"):
    
    # 告訴 Discord 正在處理中，避免 3 秒超時
    await interaction.response.defer()

    # 組合給 Gemini 的提示詞 (Prompt)
    prompt = (
        f"你是一位親切的五星級主廚。請根據以下條件提供食譜：\n"
        f"- 食材：{ingredients}\n"
        f"- 料理風格：{style}\n"
        f"- 烹飪方式：{method}\n"
        f"輸出的內容應包含：菜名、預估時間、難易度、食材清單、詳細步驟。"
    )

    try:
        # 4. 呼叫 Gemini API
        response = model.generate_content(prompt)
        recipe = response.text
        
        # 回傳結果
        await interaction.followup.send(f"👨‍🍳 **Gemini 主廚為您推薦：**\n\n{recipe}")
        
    except Exception as e:
        await interaction.followup.send(f"❌ 廚房出錯了：{str(e)}")

bot.run(DISCORD_TOKEN)
