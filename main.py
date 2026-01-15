import os
import discord
from discord import app_commands
from google import genai
from google.genai import types
from dotenv import load_dotenv
from flask import Flask        # 用於建立虛擬網頁
import threading              # 用於同時執行網頁與機器人

# --- 1. 建立虛擬 Web Server 騙過 Render 的 Port 檢查 ---
app = Flask('')

@app.route('/')
def home():
    # 當 Render 訪問網址時回傳此內容
    return "Chef Bot is alive and cooking!"

def run_web():
    # Render 會自動分配一個 PORT 環境變數給 Web Service
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
# ---------------------------------------------------

# 2. 載入環境變數與初始化
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# 初始化新版 Gemini 2.0 客戶端 (Google GenAI SDK)
client = genai.Client(api_key=GEMINI_KEY)

class ChefBot(discord.Client):
    def __init__(self):
        # 設定 Discord 基本權限
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # 啟動時同步斜線指令到 Discord
        await self.tree.sync()

bot = ChefBot()

# 3. 定義 Spec 中的選單選項 (Choices)
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

# 4. 斜線指令實作 /cook
@bot.tree.command(name="cook", description="冰箱大廚：Gemini 2.0 聯網為您量身打造食譜")
@app_commands.describe(
    ingredients="請輸入現有食材（例如：雞胸肉, 洋蔥）",
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
    # 先告訴 Discord 正在處理，避免 3 秒超時
    await interaction.response.defer()

    selected_style = style.value if style else "不拘"
    selected_method = method.value if method else "不拘"

    # 5. 建立 Prompt
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
        # 6. 呼叫 Gemini 2.0 Flash API (包含 Google Search 搜尋工具)
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.7
            )
        )
        
        recipe_text = response.text

        # 7. 使用 Embed 美化 Discord 輸出
        embed = discord.Embed(
            title="👨‍🍳 冰箱大廚：今日特選菜單 (Gemini 2.0 版)",
            description=f"針對您的食材：**{ingredients}** 所設計",
            color=discord.Color.green()
        )
        embed.add_field(name="料理指南", value=recipe_text[:1024], inline=False)
        
        if len(recipe_text) > 1024:
            embed.add_field(name="料理指南 (續)", value=recipe_text[1024:2048], inline=False)

        embed.set_footer(text="本食譜結合 Gemini 2.0 Flash 與 Google Search 實時搜尋技術")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Error: {e}")
        await interaction.followup.send(f"❌ 廚房出狀況了：{str(e)}")

@bot.event
async def on_ready():
    print(f"✅ 機器人 {bot.user} 已上線！")
    print(f"🚀 正在使用 Gemini 2.0 聯網引擎...")

if __name__ == "__main__":
    # --- 關鍵：啟動 Web Server 線程 ---
    # 使用 daemon=True 確保主程式結束時網頁服務也會跟著結束
    threading.Thread(target=run_web, daemon=True).start()
    
    # 啟動 Discord 機器人
    bot.run(DISCORD_TOKEN)
