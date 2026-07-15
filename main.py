import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput
import time
import json
import os

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

# 1. لوحة الشفتات (دخول، خروج، نقاطي، توب 10)
class ShiftView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="تسجيل دخول", style=discord.ButtonStyle.green, custom_id="shift_in")
    async def clock_in(self, interaction, button):
        active_shifts[str(interaction.user.id)] = time.time()
        await interaction.response.send_message("🟢 تم تسجيل دخولك.", ephemeral=True)

    @discord.ui.button(label="تسجيل خروج", style=discord.ButtonStyle.red, custom_id="shift_out")
    async def clock_out(self, interaction, button):
        start = active_shifts.pop(str(interaction.user.id), None)
        if not start: return await interaction.response.send_message("❌ لم تسجل دخولك!", ephemeral=True)
        pts = int((time.time() - start) // 600)
        data = load_data()
        data[str(interaction.user.id)] = data.get(str(interaction.user.id), 0) + pts
        save_data(data)
        await interaction.response.send_message(f"🔴 تم الخروج. النقاط: {pts}", ephemeral=True)

    @discord.ui.button(label="نقاطي", style=discord.ButtonStyle.blurple, custom_id="my_pts")
    async def my_pts(self, interaction, button):
        pts = load_data().get(str(interaction.user.id), 0)
        await interaction.response.send_message(f"📊 نقاطك الحالية: {pts}", ephemeral=True)

    @discord.ui.button(label="توب 10", style=discord.ButtonStyle.gray, custom_id="top_10")
    async def top_10(self, interaction, button):
        data = load_data()
        sorted_d = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
        msg = "**🏆 توب 10 عساكر:**\n\n"
        for uid, pts in sorted_d:
            member = interaction.guild.get_member(int(uid))
            name = member.display_name if member else f"ID: {uid}"
            msg += f"• {name} : {pts}\n"
        await interaction.response.send_message(msg, ephemeral=True)

# 2. لوحة إدارة النقاط (إضافة/خصم)
class AdminModal(Modal, title="إدارة النقاط"):
    m_id = TextInput(label="آيدي العسكري")
    amt = TextInput(label="العدد")
    act = TextInput(label="العملية (خصم/إضافة/تصفير)")
    async def on_submit(self, interaction):
        data = load_data()
        mid, amt = str(self.m_id.value), int(self.amt.value or 0)
        if self.act.value == "خصم": data[mid] = max(0, data.get(mid, 0) - amt)
        elif self.act.value == "إضافة": data[mid] = data.get(mid, 0) + amt
        else: data[mid] = 0
        save_data(data)
        await interaction.response.send_message("✅ تمت العملية.", ephemeral=True)

class AdminControlView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚙️ إدارة النقاط", style=discord.ButtonStyle.danger, custom_id="admin_manage")
    async def manage(self, interaction, button): await interaction.response.send_modal(AdminModal())

# 3. لوحة ضبط المجرم
class CriminalModal(Modal, title="سجل ضبط مجرم"):
    name = TextInput(label="الاسم")
    charges = TextInput(label="التهم")
    async def on_submit(self, interaction):
        data = load_data()
        data[str(interaction.user.id)] = data.get(str(interaction.user.id), 0) + 10
        save_data(data)
        await interaction.response.send_message(f"🚨 تم ضبط: {self.name.value}\nالمكافأة: +10 نقاط")

class CriminalView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="👮‍♂️ ضبط مجرم", style=discord.ButtonStyle.primary, custom_id="crime_arrest")
    async def arrest(self, interaction, button): await interaction.response.send_modal(CriminalModal())

# 4. لوحة الدسباتش
class DispatchModal(Modal, title="تحديث الدسباتش"):
    d1 = TextInput(label="منشن الدسباتش")
    d2 = TextInput(label="منشن مساعد الدسباتش")
    p1 = TextInput(label="عدد المتواجدين")
    p2 = TextInput(label="عدد الغائبين")
    v1 = TextInput(label="عدد المركبات")
    async def on_submit(self, interaction):
        msg = f"**```Dispatch```**\n﹣مـنـشـن الـدسبـاتـش : - {self.d1.value}\n﹣مُسـاعـد الـدسبـاتـش : - {self.d2.value}\n﹣عدد الـعساكـر الـمـتواجديـن : - {self.p1.value}\n﹣عدد الـعساكـر الـغـير مـتواجديـن: - {self.p2.value}\n﹣عدد المركبات في الميدان : - {self.v1.value}\n﹣مسؤول الفترة : - {interaction.user.mention}\n<@&1526289142466609152>"
        await interaction.response.send_message(msg)

class DispatchView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📡 تحديث الدسباتش", style=discord.ButtonStyle.secondary, custom_id="dispatch_upd")
    async def update(self, interaction, button): await interaction.response.send_modal(DispatchModal())

@bot.event
async def on_ready():
    bot.add_view(ShiftView())
    bot.add_view(AdminControlView())
    bot.add_view(CriminalView())
    bot.add_view(DispatchView())
    print("البوت جاهز!")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    await ctx.send("لوحة الشفتات:", view=ShiftView())
    await ctx.send("لوحة القادة:", view=AdminControlView())
    await ctx.send("لوحة القبض:", view=CriminalView())
    await ctx.send("لوحة الدسباتش:", view=DispatchView())

bot.run(os.environ.get('DISCORD_TOKEN'))

