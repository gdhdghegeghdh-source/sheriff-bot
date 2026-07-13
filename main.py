import discord
from discord.ext import commands
from discord.ui import Button, View
import time
import json
import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
    
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
DATA_FILE = "sheriff_points.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# قاموس لتخزين وقت دخول العساكر (مؤقت في الذاكرة)
active_shifts = {}

class ShiftView(View):
    def __init__(self):
        super().__init__(timeout=None) # عشان الأزرار ما تخرب وتخفي بعد فترة

    @discord.ui.button(label="Clock In (دخول)", style=discord.ButtonStyle.green, custom_id="clock_in")
    async def clock_in(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        if user_id in active_shifts:
            await interaction.response.send_message("❌ أنت مسجل دخول بالفعل في الشفت!", ephemeral=True)
            return
        
        active_shifts[user_id] = time.time()
        await interaction.response.send_message("🟢 تم تسجيل دخولك للشفت بنجاح. بالتوفيق يا وحش!", ephemeral=True)

    @discord.ui.button(label="Clock Out (خروج)", style=discord.ButtonStyle.red, custom_id="clock_out")
    async def clock_out(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        if user_id not in active_shifts:
            await interaction.response.send_message("❌ أنت مش مسجل دخول عشان تطلع!", ephemeral=True)
            return
        
        start_time = active_shifts.pop(user_id)
        duration_seconds = time.time() - start_time
        duration_minutes = int(duration_seconds // 60)
        
        # حساب النقاط: كل 20 دقيقة بنقطة
        points_earned = duration_minutes // 20
        
        # حفظ النقاط في الملف
        data = load_data()
        current_points = data.get(user_id, 0)
        new_points = current_points + points_earned
        data[user_id] = new_points
        save_data(data)
        
        msg = f"🔴 **تسجيل خروج شفت**\n"
        msg += f"• العسكري: {interaction.user.mention}\n"
        msg += f"• مدة الشفت: `{duration_minutes}` دقيقة\n"
        msg += f"• النقاط المكتسبة: `+{points_earned}` نقطة\n"
        msg += f"• مجموع نقاطك الحالي: `{new_points}` نقطة."
        
        await interaction.response.send_message(msg, ephemeral=False)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    bot.add_view(ShiftView()) # تفعيل الأزرار بشكل دائم

@bot.command()
@commands.has_permissions(administrator=True)
async def لوحة_الشفتات(ctx):
    embed = discord.Embed(
        title="🚨 لوحة تسجيل شفتات الشيرف",
        description="الرجاء الضغط على الزر الأخضر عند بدء الشفت، والزر الأحمر عند الانتهاء لحساب نقاطك تلقائياً.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=ShiftView())

@bot.command()
async def نقاطي(ctx):
    data = load_data()
    user_id = str(ctx.author.id)
    user_points = data.get(user_id, 0)
    await ctx.send(f"👮‍♂️ | حالياً نقاطك المسجلة هي: **{user_points}** نقطة.")
keep_alive( )
bot.run(os.environ['DISCORD_TOKEN'])
