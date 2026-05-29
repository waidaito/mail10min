import os
import io
import discord
import aiohttp
import asyncio
import re
from flask import Flask
from threading import Thread
from discord.ext import commands
from discord.ui import Button, View

TOKEN = os.getenv("TOKEN")

app = Flask('')

@app.route('/')
def home():
    return "Bot is live"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=".", 
    intents=intents,
    activity=discord.Activity(type=discord.ActivityType.watching, name="tao gmail 10p")
)

class XacNhanMailView(View):
    def __init__(self, ten_muon_dat):
        super().__init__(timeout=60)
        self.ten_muon_dat = ten_muon_dat

    @discord.ui.button(label="Xac Nhan Tao Mail", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        user = interaction.user
        
        try:
            dm_channel = await user.create_dm()
        except:
            await interaction.followup.send("Khong the gui DM cho ban. Vui long mo chan tin nhan tu nguoi la.", ephemeral=True)
            return

        await interaction.followup.send("Da bat dau tien trinh tao mail. Vui long kiem tra (DM) cua ban.", ephemeral=True)
        self.stop()

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.guerrillamail.com/ajax.php?f=get_email_address") as resp:
                if resp.status != 200:
                    await dm_channel.send("Khong the ket noi loi")
                    return
                
                data = await resp.json()
                sid_token = data.get("sid_token")
                email_address = data.get("email_addr")

            if self.ten_muon_dat:
                set_url = f"https://api.guerrillamail.com/ajax.php?f=set_email_user&email_user={self.ten_muon_dat}&sid_token={sid_token}"
                async with session.get(set_url) as set_resp:
                    if set_resp.status == 200:
                        set_data = await set_resp.json()
                        email_address = set_data.get("email_addr")

            status_msg = await dm_channel.send(f"Email 10 phut cua ban: `{email_address}`\nDang cho tin nhan den trong DM (tu dong kiem tra moi 5 giay trong 10 phut)...")
            
            seq = 0
            read_int_ids = set()
            last_embed_msg = None
            
            for _ in range(120): 
                await asyncio.sleep(5)
                
                check_url = f"https://api.guerrillamail.com/ajax.php?f=check_email&seq={seq}&sid_token={sid_token}"
                async with session.get(check_url) as check_resp:
                    if check_resp.status == 200:
                        check_data = await check_resp.json()
                        messages = check_data.get("list", [])
                        seq = check_data.get("seq", seq)
                        
                        for mail_info in messages:
                            email_id = mail_info.get("mail_id")
                            
                            if email_id in read_int_ids:
                                continue
                                
                            read_int_ids.add(email_id)

                            fetch_url = f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={email_id}&sid_token={sid_token}"
                            async with session.get(fetch_url) as fetch_resp:
                                if fetch_resp.status == 200:
                                    msg_data = await fetch_resp.json()
                                    
                                    tieu_de_goc = msg_data.get("mail_subject", "Khong co tieu de")
                                    noi_dung_goc = msg_data.get("mail_body", "Khong co noi dung.")
                                    noi_dung_goc = re.sub(r'<[^>]*>', '', noi_dung_goc)
                                    noi_dung_goc = noi_dung_goc[:1000]
                                    
                                    embed = discord.Embed(title="Ban co thu moi!", color=discord.Color.blue())
                                    embed.add_field(name="Nguoi gui:", value=msg_data.get("mail_from"), inline=False)
                                    embed.add_field(name="Tieu de:", value=tieu_de_goc, inline=False)
                                    embed.add_field(name="Noi dung:", value=f"```\n{noi_dung_goc}\n```", inline=False)
                                    
                                    if last_embed_msg:
                                        try:
                                            await last_embed_msg.delete()
                                        except:
                                            pass
                                    
                                    last_embed_msg = await dm_channel.send(embed=embed)
                                    await status_msg.edit(content=f"Email: `{email_address}`\nDa nhan duoc thu moi nhat va da xoa thong bao cu!")
                                
            await status_msg.edit(content=f"Email: `{email_address}` da het 10 phut thoi gian cho.")

@bot.event
async def on_ready():
    print(f"Bot Mail da san sang: {bot.user.name}")

@bot.command(name="genmail")
async def generate_guerrilla_mail(ctx, ten_muon_dat: str = None):
    view = XacNhanMailView(ten_muon_dat)
    
    # Tao bang luon o day de boc dong chu thong bao lai
    embed = discord.Embed(
        title="He Thong Tao Mail", 
        description="Bam vao nut duoi day de xac nhan tao email 10 phut :", 
        color=discord.Color.green()
    )
    
    await ctx.send(embed=embed, view=view)

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
                                    
