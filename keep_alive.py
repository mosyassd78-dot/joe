import discord
from discord.ext import commands
from discord import AuditLogAction

# 1. إعداد النيات (Intents)
# يجب تفعيل هذه النيات في بوابة مطوري ديسكورد
intents = discord.Intents.default()
intents.members = True          # لوغ الدخول/الخروج وتعديل الرتب
intents.message_content = True  # لوغ تعديل/حذف الرسائل
intents.moderation = True       # لوغ الباند والطرد
intents.guilds = True           # لأحداث الخادم

# يمكنك استخدام commands.Bot أو discord.Client
# نستخدم commands.Bot لتسهيل إضافة الأوامر في المستقبل
bot = commands.Bot(command_prefix='!', intents=intents)

# 2. إعداد قنوات السجلات (Log Channel IDs)
# **يجب عليك تغيير هذه الأرقام إلى ID القنوات المخصصة للسجلات في خادمك**
LOG_CHANNEL_ID = 123456789012345678 # قناة السجل العامة
MOD_LOG_CHANNEL_ID = 987654321098765432 # قناة سجلات الإشراف (الباند)

@bot.event
async def on_ready():
    """يتم تشغيل هذا الحدث عندما يصبح البوت جاهزًا"""
    print(f'تم تسجيل الدخول كـ {bot.user}')
    print(f'ID البوت: {bot.user.id}')

# --- 3. سجلات الأعضاء والرسائل (Member and Message Logs) ---

@bot.event
async def on_member_join(member):
    """لوغ دخول عضو جديد"""
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title="📥 دخول عضو جديد",
            description=f"**العضو:** {member.mention} (`{member}`)\n**تاريخ الإنشاء:** {member.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    """لوغ خروج/طرد عضو"""
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title="📤 خروج/مغادرة عضو",
            description=f"**العضو:** {member.mention} (`{member}`)\n**ID:** `{member.id}`",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    """لوغ حذف رسالة"""
    # نتجاهل رسائل البوت لمنع التسجيلات الذاتية
    if message.author.bot:
        return
    # نتجاهل إذا لم يكن محتوى الرسالة موجودًا في الكاش
    if message.content is None and not message.attachments:
        return
    
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel and message.guild:
        # إذا كانت الرسالة قديمة جدًا وغير موجودة في الكاش، لن يتم تسجيل المحتوى
        content = message.content or "**لا يمكن استرداد المحتوى (غير موجود في الكاش)**"
        
        embed = discord.Embed(
            title="🗑️ حذف رسالة",
            description=f"**المرسل:** {message.author.mention} (`{message.author}`)\n**في القناة:** {message.channel.mention}",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="المحتوى المحذوف", value=f"```\n{content[:1024]}...\n```" if len(content) > 1024 else f"```\n{content}\n```", inline=False)
        
        # إضافة المرفقات إذا وجدت
        if message.attachments:
            attachments_list = "\n".join([a.url for a in message.attachments])
            embed.add_field(name="المرفقات", value=attachments_list, inline=False)
            
        embed.set_footer(text=f"ID الرسالة: {message.id}")
        await log_channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    """لوغ تعديل رسالة"""
    # نتجاهل رسائل البوت
    if before.author.bot:
        return
    # نتجاهل التعديلات التي لا تغير المحتوى (مثل تضمين رابط)
    if before.content == after.content:
        return

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel and before.guild:
        embed = discord.Embed(
            title="📝 تعديل رسالة",
            description=f"**المرسل:** {before.author.mention} (`{before.author}`)\n**في القناة:** {before.channel.mention}\n[انقر للانتقال للرسالة]({after.jump_url})",
            color=discord.Color.orange()
        )
        embed.add_field(name="قبل التعديل", value=f"```\n{before.content[:1024]}\n```", inline=False)
        embed.add_field(name="بعد التعديل", value=f"```\n{after.content[:1024]}\n```", inline=False)
        
        embed.set_footer(text=f"ID الرسالة: {before.id}")
        await log_channel.send(embed=embed)

# --- 4. سجلات الرتب (Role Logs) ---

@bot.event
async def on_member_update(before, after):
    """لوغ تعديل رتب عضو"""
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        # التحقق من تغيير الرتب
        if before.roles != after.roles:
            added_roles = [role.name for role in after.roles if role not in before.roles]
            removed_roles = [role.name for role in before.roles if role not in after.roles]

            description = f"**العضو:** {after.mention} (`{after}`)\n**ID:** `{after.id}`"
            
            if added_roles:
                description += f"\n**➕ الرتب المضافة:** {', '.join(added_roles)}"
                color = discord.Color.blue()
            if removed_roles:
                description += f"\n**➖ الرتب المحذوفة:** {', '.join(removed_roles)}"
                color = discord.Color.gold()
            
            if added_roles or removed_roles:
                embed = discord.Embed(
                    title="🛡️ تعديل رتبة",
                    description=description,
                    color=color
                )
                await log_channel.send(embed=embed)

# --- 5. سجلات الإشراف (Moderation Logs - Ban) ---

@bot.event
async def on_member_ban(guild, user):
    """لوغ حظر (Ban) عضو"""
    log_channel = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if log_channel:
        # محاولة استرداد مدخل سجل التدقيق (Audit Log) لمعرفة المشرف والسبب
        try:
            async for entry in guild.audit_logs(limit=1, action=AuditLogAction.ban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    reason = entry.reason or "لا يوجد سبب محدد"
                    
                    embed = discord.Embed(
                        title="🔨 حظر عضو (Ban)",
                        description=f"**العضو المحظور:** {user.mention} (`{user}`)\n**ID:** `{user.id}`\n**المشرف:** {moderator.mention}\n**السبب:** {reason}",
                        color=discord.Color.from_rgb(170, 0, 0) # لون أحمر داكن
                    )
                    await log_channel.send(embed=embed)
                    return
        except discord.Forbidden:
            # إذا لم يكن لدى البوت صلاحية قراءة سجل التدقيق
            embed = discord.Embed(
                title="🔨 حظر عضو (Ban)",
                description=f"**العضو المحظور:** {user.mention} (`{user}`)\n**ID:** `{user.id}`\n**المشرف:** `لم يتمكن البوت من تحديد المشرف (نقص في الصلاحيات)`",
                color=discord.Color.from_rgb(170, 0, 0)
            )
            await log_channel.send(embed=embed)
            
# --- 6. تشغيل البوت ---

# **يجب عليك تغيير هذا إلى توكن (Token) البوت الخاص بك**
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE" 

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
