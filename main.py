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

def send_log(title, embed):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        bot.loop.create_task(channel.send(embed=embed))

# --- لوحة الشفتات ---
class ShiftView(View):
    def __init__(self): super().__init__(timeout=None)
    
    @discord.ui.button(label="🟢 دخول", style=discord.ButtonStyle.green, custom_id="shift_in_final")
    async def clock_in(self, interaction, button):
        active_shifts[str(interaction.user.id)] = time.time()
        await interaction.response.send_message("🟢 تم تسجيل دخولك.", ephemeral=True)

    @discord.ui.button(label="🔴 خروج", style=discord.ButtonStyle.red, custom_id="shift_out_final")
    async def clock_out(self, interaction, button):
        start = active_shifts.pop(str(interaction.user.id), None)
        if not start: return await interaction.response.send_message("❌ لم تسجل دخولك!", ephemeral=True)
        pts = int((time.time() - start) // 600)
        data = load_data()
        data[str(interaction.user.id)] = data.get(str(interaction.user.id), 0) + pts
        save_data(data)
        await interaction.response.send_message(f"🔴 تم الخروج. النقاط المكتسبة: {pts}", ephemeral=True)

    @discord.ui.button(label="📊 نقاطي", style=discord.ButtonStyle.blurple, custom_id="my_pts_final")
    async def my_pts(self, interaction, button):
        pts = load_data().get(str(interaction.user.id), 0)
        await interaction.response.send_message(f"📊 نقاطك الحالية: {pts}", ephemeral=True)

    @discord.ui.button(label="📋 المباشرين", style=discord.ButtonStyle.secondary, custom_id="active_list_final")
    async def show_active(self, interaction, button):
        if not active_shifts: return await interaction.response.send_message("❌ لا يوجد عساكر بالخدمة.", ephemeral=True)
        users = [f"<@{uid}>" for uid in active_shifts.keys()]
        await interaction.response.send_message("👮‍♂️ قائمة المباشرين:\n" + "\n".join(users), ephemeral=True)

# --- لوحة القادة ---
class AdminModal(Modal, title="إدارة النقاط"):
    m_id = TextInput(label="آيدي العسكري")
    act = TextInput(label="العملية (خصم/إضافة/تصفير)")
    reason = TextInput(label="القيمة")
    async def on_submit(self, interaction):
        mid = get_clean_id(self.m_id.value)
        data = load_data()
        val = int(self.reason.value) if self.reason.value.isdigit() else 1
        if self.act.value == "تصفير": data[mid] = 0
        elif self.act.value == "إضافة": data[mid] = data.get(mid, 0) + val
        elif self.act.value == "خصم": data[mid] = data.get(mid, 0) - val
        save_data(data)
        await interaction.response.send_message(f"✅ تم تحديث نقاط <@{mid}>", ephemeral=True)

class AdminControlView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚙️ إدارة النقاط", style=discord.ButtonStyle.danger, custom_id="admin_manage_final")
    async def manage(self, interaction, button): await interaction.response.send_modal(AdminModal())
    @discord.ui.button(label="🏆 المتصدرين", style=discord.ButtonStyle.primary, custom_id="top_list_final")
    async def top_list(self, interaction, button):
        data = load_data()
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
        msg = "🏆 أعلى 10 عساكر:\n" + "\n".join([f"<@{uid}>: {pts}" for uid, pts in sorted_data])
        await interaction.response.send_message(msg, ephemeral=True)

# --- لوحة القبض ---
class CriminalModal(Modal, title="سجل القبض"):
    name = TextInput(label="اسم المجرم")
    id_num = TextInput(label="هوية المجرم")
    items = TextInput(label="الممنوعات", style=discord.TextStyle.paragraph)
    img_url = TextInput(label="رابط صورة المجرم")
    duration = TextInput(label="مدة السجن")
    async def on_submit(self, interaction):
        dur = int(self.duration.value)
        pts = 6 if dur <= 40 else 10 if dur <= 80 else 12 if dur <= 180 else 15
        data = load_data()
        data[str(interaction.user.id)] = data.get(str(interaction.user.id), 0) + pts
        save_data(data)
        embed = discord.Embed(title="🚨 بلاغ قبض", color=discord.Color.red())
        embed.add_field(name="العسكري", value=interaction.user.mention, inline=False)
        embed.add_field(name="المجرم", value=self.name.value, inline=True)
        embed.add_field(name="الهوية", value=self.id_num.value, inline=True)
        embed.add_field(name="الممنوعات", value=self.items.value, inline=False)
        embed.set_image(url=self.img_url.value)
        await interaction.response.send_message("✅ تم تسجيل القبض!", ephemeral=True)
        send_log("سجل القبض", embed)

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

