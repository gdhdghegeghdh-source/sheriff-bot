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

# --- لوحة الشفتات المدمجة ---
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
        # تم ضبط المعادلة: 600 ثانية = 10 دقائق = 1 نقطة
        pts = int((time.time() - start) // 600)
        data = load_data()
        data[str(interaction.user.id)] = data.get(str(interaction.user.id), 0) + pts
        save_data(data)
        await interaction.response.send_message(f"🔴 تم الخروج. النقاط المكتسبة: {pts}", ephemeral=True)

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

# --- لوحة الدسباتش ---
class DispatchModal(Modal, title="تحديث الدسباتش"):
    d1 = TextInput(label="منشن الدسباتش")
    d2 = TextInput(label="منشن مساعد الدسباتش")
    p1 = TextInput(label="عدد المتواجدين")
    p2 = TextInput(label="عدد الغائبين")
    v1 = TextInput(label="عدد المركبات")

    async def on_submit(self, interaction):
        msg = f"""**```Dispatch```**
﹣مـنـشـن الـدسبـاتـش : - {self.d1.value}
﹣مُسـاعـد الـدسبـاتـش : - {self.d2.value}
﹣عدد الـعساكـر الـمـتواجديـن : - {self.p1.value}
﹣عدد الـعساكـر الـغـير مـتواجديـن: - {self.p2.value}
﹣عدد المركبات في الميدان : - {self.v1.value}
﹣مسؤول الفترة : - {interaction.user.mention}
<@&1526289142466609152>"""
        await interaction.response.send_message(msg)

class DispatchView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📡 تحديث الدسباتش", style=discord.ButtonStyle.secondary, custom_id="dispatch_upd")
    async def update(self, interaction, button): await interaction.response.send_modal(DispatchModal())

# --- تهيئة البوت ---
@bot.event
async def on_ready():
    bot.add_view(ShiftView())
    bot.add_view(DispatchView())
    print("البوت جاهز!")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    await ctx.send("لوحة الشفتات:", view=ShiftView())
    await ctx.send("لوحة الدسباتش:", view=DispatchView())

bot.run(os.environ.get('DISCORD_TOKEN'))
 
