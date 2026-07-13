import discord
from discord.ext import commands
from discord.ui import Button, View
import time
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

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

active_shifts = {}

class ShiftView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تسجيل دخول", style=discord.ButtonStyle.green, custom_id="clock_in")
    async def clock_in(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        if user_id in active_shifts:
            await interaction.response.send_message("❌ أنت مسجل دخول بالفعل!", ephemeral=True)
            return
        active_shifts[user_id] = time.time()
        await interaction.response.send_message("🟢 تم تسجيل الدخول.", ephemeral=True)

    @discord.ui.button(label="تسجيل خروج", style=discord.ButtonStyle.red, custom_id="clock_out")
    async def clock_out(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        if user_id not in active_shifts:
            await interaction.response.send_message("❌ أنت غير مسجل دخول!", ephemeral=True)
            return
        
        start_time = active_shifts.pop(user_id)
        duration_minutes = int((time.time() - start_time) // 60)
        points_earned = duration_minutes // 20
        
        data = load_data()
        new_points = data.get(user_id, 0) + points_earned
        data[user_id] = new_points
        save_data(data)
        
        await interaction.response.send_message(f"🔴 **تسجيل خروج**\n• العسكري: {interaction.user.mention}\n• المدة: {duration_minutes} دقيقة\n• النقاط المكتسبة: +{points_earned}\n• المجموع الكلي: {new_points}", ephemeral=False)

    @discord.ui.button(label="نقاطي", style=discord.ButtonStyle.blurple, custom_id="my_points")
    async def my_points(self, interaction: discord.Interaction, button: Button):
        data = load_data()
        pts = data.get(str(interaction.user.id), 0)
        await interaction.response.send_message(f"👮‍♂️ نقاطك الحالية: **{pts}** نقطة.", ephemeral=True)

    @discord.ui.button(label="ترتيب العساكر", style=discord.ButtonStyle.secondary, custom_id="leaderboard")
    async def leaderboard(self, interaction: discord.Interaction, button: Button):
        data = load_data()
        if not data:
            await interaction.response.send_message("لا توجد بيانات نقاط حالياً.", ephemeral=True)
            return
        sorted_data = sorted(data.items(), key=lambda item: item[1], reverse=True)[:10]
        msg = "🏆 **أعلى 10 عساكر بالنقاط:**\n"
        for i, (uid, pts) in enumerate(sorted_data):
            msg += f"{i+1}. <@{uid}>: **{pts}** نقطة\n"
        await interaction.response.send_message(msg, ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(ShiftView())

@bot.command()
@commands.has_permissions(administrator=True)
async def لوحة_الشفتات(ctx):
    embed = discord.Embed(title="🚨 لوحة تسجيل شفتات الشيرف", description="استخدم الأزرار أدناه للتحكم بشفتك ونقاطك.", color=discord.Color.blue())
    await ctx.send(embed=embed, view=ShiftView())

@bot.command()
@commands.has_permissions(administrator=True)
async def تعديل_نقاط(ctx, member: discord.Member, amount: int):
    data = load_data()
    data[str(member.id)] = data.get(str(member.id), 0) + amount
    save_data(data)
    await ctx.send(f"✅ تم تعديل نقاط {member.mention}، المجموع الجديد: {data[str(member.id)]} نقطة.")

bot.run(os.environ['DISCORD_TOKEN'])
 
