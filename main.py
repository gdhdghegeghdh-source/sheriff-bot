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

def send_log(interaction, title, description):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=f"📝 {title}", description=description, color=discord.Color.blue())
        embed.set_footer(text=f"بواسطة: {interaction.user.display_name}")
        bot.loop.create_task(channel.send(embed=embed))

class ShiftView(View):
    def __init__(self): super().__init__(timeout=None)
    
    @discord.ui.button(label="🟢 دخول الشفت", style=discord.ButtonStyle.green, custom_id="shift_in_final")
    async def clock_in(self, interaction, button):
        active_shifts[str(interaction.user.id)] = time.time()
        await interaction.response.edit_message(content="🟢 تم تسجيل دخولك.", embed=None)

    @discord.ui.button(label="🔴 خروج الشفت", style=discord.ButtonStyle.red, custom_id="shift_out_final")
    async def clock_out(self, interaction, button):
        start = active_shifts.pop(str(interaction.user.id), None)
        if not start: return await interaction.response.edit_message(content="❌ لم تسجل دخولك!", embed=None)
        pts = int((time.time() - start) // 600)
        data = load_data()
        data[str(interaction.user.id)] = data.get(str(interaction.user.id), 0) + pts
        save_data(data)
        await interaction.response.edit_message(content=f"🔴 تم الخروج. النقاط المكتسبة: {pts}", embed=None)

    @discord.ui.button(label="📊 نقاطي", style=discord.ButtonStyle.blurple, custom_id="my_pts_final")
    async def my_pts(self, interaction, button):
        pts = load_data().get(str(interaction.user.id), 0)
        embed = discord.Embed(title="📊 استعلام النقاط", description=f"نقاطك الحالية هي: {pts}", color=discord.Color.gold())
        await interaction.response.edit_message(content="", embed=embed)

class AdminModal(Modal, title="إدارة النقاط"):
    m_id = TextInput(label="آيدي العسكري")
    act = TextInput(label="العملية (خصم/إضافة/تصفير)")
    reason = TextInput(label="الكمية أو السبب")
    
    async def on_submit(self, interaction):
        mid = get_clean_id(self.m_id.value)
        data = load_data()
        val = int(self.reason.value) if self.reason.value.isdigit() else 1
        
        if self.act.value == "تصفير": data[mid] = 0
        elif self.act.value == "إضافة": data[mid] = data.get(mid, 0) + val
        elif self.act.value == "خصم": data[mid] = data.get(mid, 0) - val
        
        save_data(data)
        await interaction.response.send_message(f"✅ تم تحديث نقاط <@{mid}>", ephemeral=True)
        send_log(interaction, "إدارة نقاط", f"العسكري: <@{mid}>\nالعملية: {self.act.value}\nالقيمة: {val}")

class AdminControlView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚙️ إدارة النقاط", style=discord.ButtonStyle.danger, custom_id="admin_manage_final")
    async def manage(self, interaction, button): await interaction.response.send_modal(AdminModal())

class CriminalModal(Modal, title="سجل القبض"):
    name = TextInput(label="اسم المجرم")
    duration = TextInput(label="مدة السجن (بالدقائق)")
    async def on_submit(self, interaction):
        dur = int(self.duration.value)
        pts = 6 if dur <= 40 else 10 if dur <= 80 else 12 if dur <= 180 else 15
        data = load_data()
        uid = str(interaction.user.id)
        data[uid] = data.get(uid, 0) + pts
        save_data(data)
        await interaction.response.send_message(f"✅ تم القبض! أضيفت لك {pts} نقطة.", ephemeral=True)

class FinalCriminalView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="👮‍♂️ القبض على المجرم", style=discord.ButtonStyle.primary, custom_id="arrest_final")
    async def arrest(self, interaction, button): await interaction.response.send_modal(CriminalModal())

@bot.event
async def on_ready():
    bot.add_view(ShiftView())
    bot.add_view(AdminControlView())
    bot.add_view(FinalCriminalView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_shifts(ctx): await ctx.send("لوحة الشفتات:", view=ShiftView())
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_admin(ctx): await ctx.send("لوحة القادة:", view=AdminControlView())
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_crime(ctx): await ctx.send("لوحة القبض:", view=FinalCriminalView())

bot.run(os.environ.get('DISCORD_TOKEN'))

