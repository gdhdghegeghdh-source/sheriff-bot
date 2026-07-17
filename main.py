import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput
import time
import json
import os
import re

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "sheriff_points.json"
LOG_CHANNEL_ID = 1526701722141982773
active_shifts = {}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

def get_clean_id(id_str):
    return re.sub(r'\D', '', str(id_str))

def send_log(interaction, title, embed):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        bot.loop.create_task(channel.send(embed=embed))

# --- لوحة الشفتات ---
class ShiftView(View):
    def __init__(self): super().__init__(timeout=None)
    
    @discord.ui.button(label="🟢 دخول", style=discord.ButtonStyle.green, custom_id="shift_in_v6")
    async def clock_in(self, interaction, button):
        active_shifts[str(interaction.user.id)] = time.time()
        await interaction.response.send_message("🟢 تم تسجيل دخولك.", ephemeral=True)

    @discord.ui.button(label="🔴 خروج", style=discord.ButtonStyle.red, custom_id="shift_out_v6")
    async def clock_out(self, interaction, button):
        start = active_shifts.pop(str(interaction.user.id), None)
        if not start: return await interaction.response.send_message("❌ لم تسجل دخولك!", ephemeral=True)
        pts = int((time.time() - start) // 600) # نقطة لكل 10 دقائق
        data = load_data()
        data[str(interaction.user.id)] = data.get(str(interaction.user.id), 0) + pts
        save_data(data)
        await interaction.response.send_message(f"🔴 تم الخروج. النقاط المكتسبة: {pts}", ephemeral=True)

    @discord.ui.button(label="📊 نقاطي", style=discord.ButtonStyle.blurple, custom_id="my_pts_v6")
    async def my_pts(self, interaction, button):
        pts = load_data().get(str(interaction.user.id), 0)
        await interaction.response.send_message(f"📊 نقاطك المحدثة: {pts}", ephemeral=True)

# --- لوحة القبض المحدثة ---
class CriminalModal(Modal, title="سجل القبض على المجرم"):
    name = TextInput(label="اسم المجرم")
    id_num = TextInput(label="هوية المجرم")
    items = TextInput(label="الممنوعات", style=discord.TextStyle.paragraph)
    img_url = TextInput(label="رابط صورة المجرم")
    duration = TextInput(label="مدة السجن (بالدقائق)")
    
    async def on_submit(self, interaction):
        dur = int(self.duration.value)
        pts = 6 if dur <= 40 else 10 if dur <= 80 else 12 if dur <= 180 else 15
        data = load_data()
        uid = str(interaction.user.id)
        data[uid] = data.get(uid, 0) + pts
        save_data(data)
        
        embed = discord.Embed(title="🚨 بلاغ قبض", color=discord.Color.red())
        embed.add_field(name="العسكري", value=interaction.user.mention, inline=False)
        embed.add_field(name="المجرم", value=self.name.value, inline=True)
        embed.add_field(name="الهوية", value=self.id_num.value, inline=True)
        embed.add_field(name="الممنوعات", value=self.items.value, inline=False)
        embed.add_field(name="النقاط المكتسبة", value=str(pts), inline=True)
        embed.set_image(url=self.img_url.value)
        
        await interaction.response.send_message(f"✅ تم تسجيل القبض!", ephemeral=True)
        send_log(interaction, "سجل القبض", embed)

class FinalCriminalView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="👮‍♂️ القبض على المجرم", style=discord.ButtonStyle.primary, custom_id="arrest_v6")
    async def arrest(self, interaction, button): await interaction.response.send_modal(CriminalModal())

@bot.event
async def on_ready():
    bot.add_view(ShiftView())
    bot.add_view(FinalCriminalView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_shifts(ctx): await ctx.send("لوحة الشفتات:", view=ShiftView())
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_crime(ctx): await ctx.send("لوحة القبض:", view=FinalCriminalView())

bot.run(os.environ.get('DISCORD_TOKEN'))

