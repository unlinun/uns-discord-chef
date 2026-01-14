import os
import discord
from discord import app_commands
# 這裡改用全新的 Google GenAI SDK
from genai import Client, types 
from dotenv import load_dotenv

# 1. 初始化與設定
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# 初始化新版 Gemini 2.0 客戶端
client = Client(api_key=GEMINI_KEY)

class ChefBot(discord.Client):
    def __init__(self):
        # 這裡照舊
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = ChefBot()

# 2. 定義 Spec 中的選項 (不變)
COOKING_STYLES = [
    app_commands.Choice(name="中式", value="中式"),
    app_commands.Choice(name="日式", value="日式"),
    app_commands.Choice(name="韓式", value="韓式"),
    app_commands.Choice(name="泰式", value="泰式"),
    app_commands.Choice(name="西式", value="西式")
]

COOKING_METHODS = [
    app_commands.Choice(name="蒸", value="蒸"),
    app_commands.Choice(name="炸", value="炸"),
    app_commands.Choice(name="炒", value="炒"),
    app_commands.Choice(name="烤", value="烤"),
    app_commands.Choice(name="煮/燉", value="煮/燉"),
    app_commands.Choice(name="涼拌", value="涼拌"),
    app_commands.Choice(name="氣炸", value="氣炸")
]

# 3. 斜線指令實作
@bot.tree.command(name="cook", description="冰箱大廚根據食材與風格為您上菜")
@app_commands.describe(
    ingredients="請輸入現有食材（例如：牛肉, 洋蔥）",
    style="想要的料理風格",
    method="偏好的烹飪方式",
    dietary="是否有忌口或過敏（例如：不吃辣）"
)
@app_commands.choices(style=COOKING_STYLES, method=COOKING_METHODS)
async def cook(
    interaction: discord.Interaction, 
    ingredients: str, 
    style: app_commands.Choice[str] = None,
    method: app_commands.Choice[str] = None,
    dietary: str = "無"
):
    await interaction.response.defer()

    selected_style = style.value if style else "不拘"
    selected_method = method.value if method else "不拘"

    # 4. 建立 Prompt (保留原始 Spec)
    prompt = f"""
    你是一位專業的五星級大廚『冰箱救星』。
    請根據以下條件設計一份食譜：
    - 食材：{ingredients}
    - 料理風格：{selected_style}
    - 烹飪方式：{selected_method}
    - 忌口限制：{dietary}

    請嚴格遵守以下輸出格式：
    # [菜名]
    ⏱ 烹飪時間：[時間]
    📊 難易度：[簡單/中等/大廚挑戰]
    📍 料理方式：{selected_method}
    
    ## 🛒 食材清單
    [列出食材]
    
    ## 👨‍🍳 料理步驟
    1. [步驟 1]
    2. [步驟 2]...
    
    💡 主廚悄悄話：[提供一個專業小技巧]
    """

    try:
        # 5. 換成您要求的新版 Gemini 2.0 呼叫方式 (含 Google Search)
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.7
            )
        )
        
        recipe_text = response.text

        # 6. 使用 Embed 美化輸出
        embed = discord.Embed(
            title="👨‍🍳 冰箱大廚：今日特選菜單 (Gemini 2.0)",
            description=f"針對您的食材：**{ingredients}** 所設計",
            color=discord.Color.green()
        )
        embed.add_field(name="料理指南", value=recipe_text, inline=False)
        embed.set_footer(text="本食譜由 Gemini 2.0 Flash 與 Google Search 技術支援")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ 廚房出狀況了：{str(e)}")

if __name__ == "__main__":
    print("🚀 冰箱大廚正在準備開張 (Gemini 2.0 版)...")
    bot.run(DISCORD_TOKEN)
