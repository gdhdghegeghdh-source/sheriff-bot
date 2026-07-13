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
active_shifts = {}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

class ShiftView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تسجيل دخول شفت", style=discord.ButtonStyle.green, custom_id="shift_start")
    async def start_shift(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        active_shifts[user_id] = time.time()
        
        log_msg = f"🟢 **تسجيل دخول شفت**\n• العسكري: {interaction.user.mention}\n• الوقت: <t:{int(time.time())}:F>"
        await interaction.channel.send(log_msg)
        await interaction.response.send_message("تم تسجيل دخولك بنجاح!", ephemeral=True)

    @discord.ui.button(label="تسجيل خروج شفت", style=discord.ButtonStyle.red, custom_id="shift_end")
    async def end_shift(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        
        if user_id not in active_shifts:
            await interaction.response.send_message("أنت لم تسجل دخولك بالشفت أصلاً!", ephemeral=True)
            return
            
        start_time = active_shifts.pop(user_id)
        duration_minutes = int((time.time() - start_time) / 60)
        
        points_earned = max(1, int(duration_minutes / 10)) 
        
        data = load_data()
        current_points = data.get(user_id, 0)
        new_points = current_points + points_earned
        data[user_id] = new_points
        save_data(data)
        
        log_msg = f"🔴 **تسجيل خروج شفت**\n"
        log_msg += f"• العسكري: {interaction.user.mention}\n"
        log_msg += f"• مدة الشفت: `{duration_minutes} دقيقة`\n"
        log_msg += f"• النقاط المكتسبة: `+{points_earned}`\n"
        log_msg += f"• مجموع نقاطك الحالي: `{new_points}`"
        
        await interaction.channel.send(log_msg)
        await interaction.response.send_message("تم تسجيل خروجك وحساب نقاطك!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    bot.add_view(ShiftView())

@bot.command()
@commands.has_permissions(administrator=True)
async def لوحة_الشفتات(ctx):
    embed = discord.Embed(
        title="🚨 لوحة تسجيل شفتات الشيرف",
        description="اضغط على الأزرار بالأسفل لتسجيل حضورك وغيابك",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=ShiftView())

@bot.command()
async def نقاطي(ctx):
    data = load_data()
    user_id = str(ctx.author.id)
    user_points = data.get(user_id, 0)
    await ctx.send(f"👮 | نقاطك المسجلة هي: {user_points}")

@bot.command()
@commands.has_permissions(administrator=True)
async def المباشرين(ctx):
    if not active_shifts:
        await ctx.send("❌ لا يوجد أي عسكري في الشفت حالياً.")
        return
        
    msg = "👮 **العساكر المباشرين حالياً في الشفت:**\n"
    for u_id, start_t in active_shifts.items():
        dur = int((time.time() - start_t) / 60)
        msg += f"• <@{u_id}> (مستمر منذ: `{dur} دقيقة`)\n"
    await ctx.send(msg)

keep_alive()
bot.run(os.environ['DISCORD_TOKEN'])

