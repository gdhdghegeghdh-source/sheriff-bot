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

def send_log(interaction, title, description):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=f"📝 {title}", description=description, color=discord.Color.blue())
        embed.set_footer(text=f"بواسطة: {interaction.user.display_name}")
        bot.loop.create_task(channel.send(embed=embed))

# --- 1. لوحة الشفتات ---
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
        send_log(interaction, "تسجيل خروج شفت", f"العسكري: {interaction.user.mention}\nالنقاط المكتسبة: {pts}")
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

# --- 2. لوحة إدارة النقاط ---
class AdminModal(Modal, title="إدارة النقاط"):
    m_id = TextInput(label="آيدي العسكري")
    act = TextInput(label="العملية (خصم/إضافة/تصفير)")
    reason = TextInput(label="السبب", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction):
        data = load_data()
        mid = str(self.m_id.value)
        if self.act.value == "تصفير": data[mid] = 0
        else: data[mid] = data.get(mid, 0) + (1 if self.act.value == "إضافة" else -1)
        save_data(data)
        msg = f"**⚙️ تحديث نقاط:**\n- العسكري: <@{mid}>\n- العملية: {self.act.value}\n- السبب: {self.reason.value}"
        send_log(interaction, "إدارة نقاط", msg)
        await interaction.response.send_message(msg)

class AdminControlView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚙️ إدارة النقاط", style=discord.ButtonStyle.danger, custom_id="admin_manage")
    async def manage(self, interaction, button): await interaction.response.send_modal(AdminModal())

# --- 3. لوحة القبض (المحدثة جذرياً) ---
class CriminalModal(Modal, title="سجل ضبط مجرم"):
    name = TextInput(label="اسم المجرم")
    id_num = TextInput(label="هوية المجرم")
    criminal_record = TextInput(label="السجل الجنائي", style=discord.TextStyle.paragraph)
    charges = TextInput(label="التهم", style=discord.TextStyle.paragraph)
    duration = TextInput(label="مدة الاحتجاز")
    fine = TextInput(label="الغرامة المالية")
    weapons = TextInput(label="الأسلحة الممنوعة", style=discord.TextStyle.paragraph)
    img_url = TextInput(label="رابط الصورة")
    async def on_submit(self, interaction):
        data = load_data()
        user_id = str(interaction.user.id)
        data[user_id] = data.get(user_id, 0) + 10
        save_data(data)
        embed = discord.Embed(title="🚨 بلاغ ضبط مجرم", color=discord.Color.red())
        embed.add_field(name="العسكري", value=interaction.user.mention, inline=False)
        embed.add_field(name="اسم المجرم", value=self.name.value, inline=True)
        embed.add_field(name="هوية المجرم", value=self.id_num.value, inline=True)
        embed.add_field(name="السجل الجنائي", value=self.criminal_record.value, inline=False)
        embed.add_field(name="التهم", value=self.charges.value, inline=False)
        embed.add_field(name="مدة الاحتجاز", value=self.duration.value, inline=True)
        embed.add_field(name="الغرامة المالية", value=self.fine.value, inline=True)
        embed.add_field(name="الأسلحة الممنوعة", value=self.weapons.value, inline=False)
        embed.set_image(url=self.img_url.value)
        send_log(interaction, "ضبط مجرم", f"العسكري: {interaction.user.mention} (+10 نقاط)\nالمجرم: {self.name.value}")
        await interaction.response.send_message(embed=embed)

class CriminalViewV2(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="👮‍♂️ ضبط مجرم", style=discord.ButtonStyle.primary, custom_id="crime_arrest_final")
    async def arrest(self, interaction, button): await interaction.response.send_modal(CriminalModal())

# --- 4. لوحة الدسباتش ---
class DispatchModal(Modal, title="تحديث الدسباتش"):
    d1 = TextInput(label="منشن الدسباتش")
    d2 = TextInput(label="منشن مساعد الدسباتش")
    p1 = TextInput(label="عدد المتواجدين")
    p2 = TextInput(label="عدد الغائبين")
    v1 = TextInput(label="عدد المركبات")
    async def on_submit(self, interaction):
        msg = f"**```Dispatch```**\n﹣مـنـشـن الـدسبـاتـش : - {self.d1.value}\n﹣مُسـاعـد الـدسبـاتـش : - {self.d2.value}\n﹣عدد الـعساكـر الـمـتواجديـن : - {self.p1.value}\n﹣عدد الـعساكـر الـغـير مـتواجديـن: - {self.p2.value}\n﹣عدد المركبات في الميدان : - {self.v1.value}\n﹣مسؤول الفترة : - {interaction.user.mention}\n<@&1526289142466609152>"
        send_log(interaction, "تحديث دسباتش", f"تم تحديث الدسباتش بواسطة {interaction.user.mention}")
        await interaction.response.send_message(msg)

class DispatchView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📡 تحديث الدسباتش", style=discord.ButtonStyle.secondary, custom_id="dispatch_upd")
    async def update(self, interaction, button): await interaction.response.send_modal(DispatchModal())

@bot.event
async def on_ready():
    bot.add_view(ShiftView())
    bot.add_view(AdminControlView())
    bot.add_view(CriminalViewV2())
    bot.add_view(DispatchView())
    print("البوت يعمل!")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_shifts(ctx): await ctx.send("لوحة الشفتات:", view=ShiftView())
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_admin(ctx): await ctx.send("لوحة القادة:", view=AdminControlView())
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_crime(ctx): await ctx.send("لوحة القبض:", view=CriminalViewV2())
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_dispatch(ctx): await ctx.send("لوحة الدسباتش:", view=DispatchView())

bot.run(os.environ.get('DISCORD_TOKEN'))

