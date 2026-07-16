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
    @discord.ui.button(label="🟢 دخول الشفت", style=discord.ButtonStyle.green, custom_id="shift_in_v4")
    async def clock_in(self, interaction, button):
        active_shifts[str(interaction.user.id)] = time.time()
        await interaction.response.send_message("🟢 تم تسجيل دخولك.", ephemeral=True)

    @discord.ui.button(label="🔴 خروج الشفت", style=discord.ButtonStyle.red, custom_id="shift_out_v4")
    async def clock_out(self, interaction, button):
        start = active_shifts.pop(str(interaction.user.id), None)
        if not start: return await interaction.response.send_message("❌ لم تسجل دخولك!", ephemeral=True)
        pts = int((time.time() - start) // 600)
        data = load_data()
        uid = str(interaction.user.id)
        data[uid] = data.get(uid, 0) + pts
        save_data(data)
        send_log(interaction, "شفت عسكري", f"العسكري: {interaction.user.mention}\nالنقاط المكتسبة: {pts}")
        await interaction.response.send_message(f"🔴 تم الخروج. النقاط: {pts}", ephemeral=True)

    @discord.ui.button(label="📊 استعلام نقاطي", style=discord.ButtonStyle.blurple, custom_id="my_pts_v4")
    async def my_pts(self, interaction, button):
        data = load_data()
        pts = data.get(str(interaction.user.id), 0)
        await interaction.response.send_message(f"📊 نقاطك الحالية: {pts}", ephemeral=True)

class AdminModal(Modal, title="إدارة النقاط"):
    m_id = TextInput(label="آيدي العسكري")
    act = TextInput(label="العملية (خصم/إضافة/تصفير)")
    reason = TextInput(label="السبب")
    
    async def on_submit(self, interaction):
        data = load_data()
        mid = get_clean_id(self.m_id.value)
        if self.act.value == "تصفير": data[mid] = 0
        elif self.act.value == "إضافة": data[mid] = data.get(mid, 0) + 1
        elif self.act.value == "خصم": data[mid] = data.get(mid, 0) - 1
        save_data(data)
        await interaction.response.send_message(f"✅ تم تحديث نقاط <@{mid}>", ephemeral=True)
        send_log(interaction, "إدارة نقاط", f"العسكري: <@{mid}>\nالعملية: {self.act.value}\nالسبب: {self.reason.value}")

class AdminControlView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚙️ إدارة النقاط", style=discord.ButtonStyle.danger, custom_id="admin_manage_v4")
    async def manage(self, interaction, button): await interaction.response.send_modal(AdminModal())

class CriminalModal(Modal, title="سجل القبض على المجرم"):
    name = TextInput(label="اسم المجرم")
    id_num = TextInput(label="هوية المجرم")
    charges = TextInput(label="التهم")
    duration = TextInput(label="مدة السجن (بالدقائق)")
    
    async def on_submit(self, interaction):
        try:
            dur = int(self.duration.value)
            if 1 <= dur <= 40: pts = 6
            elif 41 <= dur <= 80: pts = 10
            elif 81 <= dur <= 180: pts = 12
            elif 181 <= dur <= 280: pts = 15
            else: pts = 5
        except: pts = 5
        data = load_data()
        uid = str(interaction.user.id)
        data[uid] = data.get(uid, 0) + pts
        save_data(data)
        await interaction.response.send_message(f"✅ تم تسجيل القبض! أضيفت لك {pts} نقطة.", ephemeral=True)
        send_log(interaction, "عملية قبض", f"العسكري: {interaction.user.mention}\nالمجرم: {self.name.value}\nالنقاط: {pts}")

class FinalCriminalView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="👮‍♂️ القبض على المجرم", style=discord.ButtonStyle.primary, custom_id="arrest_criminal_v5")
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
 
