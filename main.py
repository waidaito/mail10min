import os
import io
import discord
import aiohttp
import asyncio
import re
from flask import Flask
from threading import Thread
from discord.ext import commands

TOKEN = os.getenv("TOKEN")

app = Flask('')

@app.route('/')
def home():
    return "Bot Mail is live"

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
    activity=discord.Activity(type=discord.ActivityType.watching, name="Guerrilla Mail")
)

@bot.event
async def on_ready():
    print(f"Bot Mail da san sang: {bot.user.name}")

@bot.command(name="genmail")
async def generate_guerrilla_mail(ctx, ten_muon_dat: str = None):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.guerrillamail.com/ajax.php?f=get_email_address") as resp:
            if resp.status != 200:
                await ctx.send("Khong the ket noi den may chu Guerrilla Mail.")
                return
            
            data = await resp.json()
            sid_token = data.get("sid_token")
            email_address = data.get("email_addr")

        if ten_muon_dat:
            set_url = f"https://api.guerrillamail.com/ajax.php?f=set_email_user&email_user={ten_muon_dat}&sid_token={sid_token}"
            async with session.get(set_url) as set_resp:
                if set_resp.status == 200:
                    set_data = await set_resp.json()
                    email_address = set_data.get("email_addr")

        status_msg = await ctx.send(f"Email 10 phut cua ban: `{email_address}`\nDang cho tin nhan den (tu dong kiem tra moi 5 giay trong 3 phut)...")
        
        seq = 0
        for _ in range(36): 
            await asyncio.sleep(5)
            
            check_url = f"https://api.guerrillamail.com/ajax.php?f=check_email&seq={seq}&sid_token={sid_token}"
            async with session.get(check_url) as check_resp:
                if check_resp.status == 200:
                    check_data = await check_resp.json()
                    messages = check_data.get("list", [])
                    
                    if messages:
                        mail_info = messages[0]
                        email_id = mail_info.get("mail_id")
                        seq = check_data.get("seq", seq)

                        fetch_url = f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={email_id}&sid_token={sid_token}"
                        async with session.get(fetch_url) as fetch_resp:
                            if fetch_resp.status == 200:
                                msg_data = await fetch_resp.json()
                                
                                embed = discord.Embed(title="Ban co thu moi!", color=discord.Color.blue())
                                embed.add_field(name="Nguoi gui:", value=msg_data.get("mail_from"), inline=False)
                                embed.add_field(name="Tieu de:", value=msg_data.get("mail_subject"), inline=False)
                                
                                body = msg_data.get("mail_body", "Khong co noi dung.")
                                body = re.sub(r'<[^>]*>', '', body)
                                body = body[:1000]
                                
                                embed.add_field(name="Noi dung:", value=f"```\n{body}\n```", inline=False)
                                
                                await ctx.reply(embed=embed)
                                await status_msg.edit(content=f"Email: `{email_address}`\nDa nhan duoc thu thanh cong!")
                                return
                            
        await status_msg.edit(content=f"Email: `{email_address}` da het thoi gian cho ma khong co thu den.")

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
    
