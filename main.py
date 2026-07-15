import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import time
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "sheriff_points.json"
LOG_CHANNEL_ID = 1526701722141982773

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

def send_log(interaction, title, description):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=f"📝 {title}", description=description, color=discord.Color.blue())
        embed.add_field(name="بواسطة", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"التوقيت: {time.strftime('%H:%M:%S')}")
        bot.loop.create_task(channel.send(embed=embed))

class ShiftView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="تسجيل دخول", style=discord.ButtonStyle.green, custom_id="shift_clock_in")
    async def clock_in(self, interaction, button):
        active_shifts[str(interaction.user.id)] = time.time()
        await interaction.response.send_message("🟢 تم تسجيل دخولك.", ephemeral=True)
        send_log(interaction, "تسجيل دخول شفت", "تم تسجيل دخول العسكري للشفت.")

    @discord.ui.button(label="تسجيل خروج", style=discord.ButtonStyle.red, custom_id="shift_clock_out")
    async def clock_out(self, interaction, button):
        start = active_shifts.pop(str(interaction.user.id), None)
        if not start: return await interaction.response.send_message("❌ غير مسجل دخول!", ephemeral=True)
        pts = int((time.time() - start) // 1200)
        data = load_data()
        data[str(interaction.user.id)] = data.get(str(interaction.user.id), 0) + pts
        save_data(data)
        send_log(interaction, "تسجيل خروج شفت", f"المدة: {int((time.time()-start)//60)} دقيقة\nالنقاط المكتسبة: {pts}")
        await interaction.response.send_message(f"🔴 تم الخروج. النقاط: {pts}", ephemeral=True)

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
        send_log(interaction, "إدارة نقاط", f"العملية: {self.act.value}\nالعضو: <@{mid}>\nالكمية: {amt}")
        await interaction.response.send_message("✅ تمت العملية.", ephemeral=True)

class AdminControlView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚙️ إدارة النقاط", style=discord.ButtonStyle.danger, custom_id="admin_manage")
    async def manage(self, interaction, button): await interaction.response.send_modal(AdminModal())

class CriminalModal(Modal, title="سجل ضبط مجرم"):
    name = TextInput(label="الاسم")
    identity = TextInput(label="الهوية")
    charges = TextInput(label="التهم", style=discord.TextStyle.paragraph)
    duration = TextInput(label="السجن")
    fine = TextInput(label="الغرامة")
    img = TextInput(label="رابط الصورة")
    async def on_submit(self, interaction):
        data = load_data()
        data[str(interaction.user.id)] = data.get(str(interaction.user.id), 0) + 10
        save_data(data)
        send_log(interaction, "ضبط مجرم", f"المتهم: {self.name.value}\nالمكافأة: +10 نقاط")
        await interaction.response.send_message(content="<@&1525736390887997520>", embed=discord.Embed(title="بلاغ قبض", description=f"الاسم: {self.name.value}\nالتهم: {self.charges.value}").set_image(url=self.img.value))

class CriminalView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="👮‍♂️ ضبط مجرم", style=discord.ButtonStyle.primary, custom_id="crime_arrest")
    async def arrest(self, interaction, button): await interaction.response.send_modal(CriminalModal())

class DispatchModal(Modal, title="تحديث الدسباتش"):
    absent = TextInput(label="عدد الغائبين")
    async def on_submit(self, interaction):
        send_log(interaction, "تحديث دسباتش", f"عدد الغائبين: {self.absent.value}")
        await interaction.response.send_message(f"**```Dispatch```**\n\n- الغائبين: {self.absent.value}")

class DispatchView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📡 تحديث الدسباتش", style=discord.ButtonStyle.secondary, custom_id="dispatch_update")
    async def update(self, interaction, button): await interaction.response.send_modal(DispatchModal())

@bot.event
async def on_ready():
    bot.add_view(ShiftView())
    bot.add_view(AdminControlView())
    bot.add_view(CriminalView())
    bot.add_view(DispatchView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    await ctx.send("لوحة الشفتات:", view=ShiftView())
    await ctx.send("لوحة القادة:", view=AdminControlView())
    await ctx.send("لوحة القبض:", view=CriminalView())
    await ctx.send("لوحة الدسباتش:", view=DispatchView())

active_shifts = {}
bot.run(os.environ.get('DISCORD_TOKEN'))
  
