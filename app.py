from quart import Quart, redirect, request, session, render_template
import requests
import discord
from discord.ext import commands, tasks
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()
discord_token = os.getenv('DISCORD_BOT_TOKEN')
chave_secreta = os.getenv("SECRET_KEY")

app = Quart(__name__)
app.secret_key = chave_secreta


# Configurações do Discord
CLIENT_ID = "1308522364727853096"
CLIENT_SECRET = "Ma9VeUBinQ1geQFtgpc56xm7r_cZ-LZo"
REDIRECT_URI = "http://127.0.0.1:5000/discord/callback"

# Configuração do bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.typing = True
intents.presences = True
intents.reactions = True

bot_token = discord_token
bot = commands.Bot(command_prefix=".", intents=intents)

#backend
@app.route("/")
async def home():
    if "user_id" in session:
        username = session.get("username", "Usuário")
        avatar = session.get("avatar", "https://cdn.discordapp.com/embed/avatars/0.png")
        return await render_template("index.html", username=username, avatar=avatar)
    return await render_template("login.html")

@app.route("/discord/login")
async def login():
    return redirect(
        f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify"
    )

@app.route("/discord/callback")
async def callback():
    code = request.args.get("code")
    if not code:
        return "Erro ao autenticar: código ausente.", 400

    # Trocar o código por um token de acesso
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)

    if response.status_code != 200:
        return "Erro ao obter token. Verifique as configurações.", 400

    token = response.json().get("access_token")
    if not token:
        return "Erro ao obter o token de acesso.", 400

    # Obter informações do usuário
    user_response = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {token}"},
    )
    if user_response.status_code != 200:
        return "Erro ao obter dados do usuário.", 400

    user_data = user_response.json()
    user_id = user_data["id"]
    username = user_data["username"]
    avatar_hash = user_data.get("avatar")
    avatar = (
        f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"
        if avatar_hash
        else "https://cdn.discordapp.com/embed/avatars/0.png"
    )

    # Salvar dados na sessão
    session["user_id"] = user_id
    session["username"] = username
    session["avatar"] = avatar

    return redirect("/")

@app.route("/index.html")
async def index():
    if "user_id" in session:
        username = session["username"]
        avatar = session["avatar"]
        return await render_template("index.html", username=username, avatar=avatar)
    return redirect("/")

async def main():
    async with bot:
        bot.loop.create_task(app.run_task(host="0.0.0.0", port=5000))
        await bot.start(bot_token)

#codigo bot
@bot.event
async def on_ready():
    bot.add_view(PersistentView())
    print("Persistent view has been added.")
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Successfully synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')
    bot.loop.create_task(alternar_presenca())

#presença
async def alternar_presenca():
    guild_id = 1261770850915324066
    role_id = 1261813315710091264

    while True:
        # Alterna entre diferentes presenças
        activity = discord.Activity(type=discord.ActivityType.listening, name="what you need")
        await bot.change_presence(activity=activity)
        await asyncio.sleep(5)

        activity = discord.Game(name="+SHOP")
        await bot.change_presence(activity=activity)
        await asyncio.sleep(5)

        # Obtém a contagem de membros com a role
        count_membros = count_members_with_role(guild_id, role_id)
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"CLIENTS - {count_membros}")
        await bot.change_presence(activity=activity)
        await asyncio.sleep(5)

def count_members_with_role(guild_id, role_id):
    guild = bot.get_guild(guild_id)

    if not guild:
        print(f"Guild with ID {guild_id} not found.")
        return 0

    role = discord.utils.get(guild.roles, id=1261813315710091264)  # Substitua pelo ID da role

    if not role:
        print(f"Role with ID {role_id} not found in guild {guild.name}.")
        return 0

    members_with_role = [member for member in guild.members if role in member.roles]
    return len(members_with_role)

#canais de informações
#members
@tasks.loop(seconds=30)
async def atualizar_canal_members():
    CANAL_ID = 1290076086771777536
    try:
        canal = bot.get_channel(CANAL_ID)
        if canal:
            guild = canal.guild
            membros_reais = [m for m in guild.members if not m.bot]
            numero_membros_reais = len(membros_reais)
            novo_nome = f'members-{numero_membros_reais}'
            await canal.edit(name=novo_nome)
            print('-----------------------------------')
            print(f'Canal atualizado para: {novo_nome}')
        else:
            print(f"Canal com ID {CANAL_ID} não encontrado.")
    except Exception as e:
        print(f"Erro ao tentar atualizar o canal: {e}")

#clients
@tasks.loop(seconds=30)
async def atualizar_canal_clients():
    CANAL_ID = 1303719327601655828
    ROLE_ID = 1303727484965224509
    try:
        canal = bot.get_channel(CANAL_ID)
        if canal:
            guild = canal.guild
            role = guild.get_role(ROLE_ID)
            if role:
                numero_membros_com_role = len(role.members)
                novo_nome = f'clients-{numero_membros_com_role}'
                await canal.edit(name=novo_nome)
                print(f'Canal atualizado para: {novo_nome}')
            else:
                print(f"Role com ID {ROLE_ID} não encontrada no servidor {guild.name}.")
        else:
            print(f"Canal com ID {CANAL_ID} não encontrado.")
    except Exception as e:
        print(f"Erro ao tentar atualizar o canal: {e}")

#ticket command
class TicketButton(discord.ui.Button):
    def __init__(self, label, ticket_option=None, image_url=None, ticket_text=None):
        super().__init__(style=discord.ButtonStyle.grey, label=label)
        self.ticket_option = ticket_option
        self.image_url = image_url
        self.ticket_text = ticket_text

    async def callback(self, interaction: discord.Interaction):
        if self.ticket_option:
            ticket_name = f"{self.ticket_option}"
            role_to_mention = discord.utils.get(interaction.guild.roles, name="REI")
            role_mention = role_to_mention.mention
            user = interaction.user
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                role_to_mention: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            ticket_channel = await guild.create_text_channel(ticket_name, overwrites=overwrites)
            ticket_message = f"📩 **|** Hi {user.mention}! You opened the ticket {self.ticket_option}. Send all possible information about your case and wait until the {role_mention} reply."
            if self.ticket_text:
                ticket_message += f"\n\n{self.ticket_text}"
            if self.image_url:
                ticket_message += f"\n{self.image_url}"
            await ticket_channel.send(ticket_message)
            await interaction.response.send_message(f"You opened the ticket {self.ticket_option} in {ticket_channel.mention}", ephemeral=True)
            view = discord.ui.View()
            close_button = CloseButton("Close", ticket_channel.id)
            view.add_item(close_button)
            await ticket_channel.send("Click the button below to close this ticket:", view=view)
        else:
            await interaction.response.send_message("Invalid ticket option.", ephemeral=True)

class CloseButton(discord.ui.Button):
    def __init__(self, label, channel_id):
        super().__init__(style=discord.ButtonStyle.grey, label=label)
        self.channel_id = channel_id

    async def callback(self, interaction: discord.Interaction):
        ticket_channel = interaction.guild.get_channel(self.channel_id)
        if ticket_channel:
            await ticket_channel.delete()
            await interaction.response.send_message("The ticket was closed successfully.", ephemeral=True)
        else:
            await interaction.response.send_message("Unable to find ticket channel.", ephemeral=True)

class Dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(value="shopping", label="Shopping", emoji="🛒"),
            discord.SelectOption(value="support", label="Support", emoji="💳"),
            discord.SelectOption(value="doubts", label="Doubts", emoji="❔"),
        ]
        super().__init__(
            placeholder="Select an option...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="persistent_view:dropdown_help"
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] in ["shopping", "support", "doubts"]:
            selected_option = self.values[0]
            await interaction.response.defer()
            view = discord.ui.View()
            open_button = TicketButton(label=f"Open {selected_option} Ticket", ticket_option=selected_option)
            view.add_item(open_button)
            await interaction.followup.send(content=f"Press the button below to open a {selected_option} ticket", view=view, ephemeral=True)

class PersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Dropdown())

@bot.command()
async def setup(ctx):
    required_role_id = 1261789230414172211
    
    if not any(role.id == required_role_id for role in ctx.author.roles):
        await ctx.send("You do not have the required role to use this command.", delete_after=5)
        return

    embed = discord.Embed(
        title="**TICKET**",
        description="➡️ - To open a ticket, select one of the options below:",
        color=0x00FFFF
    )
    embed.add_field(name="", value="```ㅤㅤㅤㅤ! 𝘽𝙀𝙁𝙊𝙍𝙀 𝙊𝙋𝙀𝙉𝙄𝙉𝙂 !ㅤㅤㅤ```", inline=False)
    embed.add_field(name="", value="➡️ - Do not open a ticket without **NECESSITY**", inline=False)
    embed.add_field(name="", value="➡️ - Don't tag the MODERATORS, they are aware of your ticket", inline=False)
    embed.set_image(url="https://i.imgur.com/gZVmjvJ.png")

    await ctx.send(embed=embed)
    await ctx.send(view=PersistentView())

#help command
@bot.tree.command(name="helpme", description="Command that lists all commands")
async def helpme(interaction: discord.Interaction):
    embed = discord.Embed(
        title="**Command List**",
        description="Here are all available commands and their functions:",
        color=0x00FFFF
    )
    embed.add_field(name="/delete [quantity]", value="Deletes a specific number of messages in the channel (only for users with message management permissions).", inline=False)
    embed.add_field(name=".suggestion [text]", value="Send a suggestion to the suggestions channel. https://discord.com/channels/1261770850915324066/1290076086775844866", inline=False)
    await interaction.response.send_message(embed=embed)

#delete command
@bot.tree.command(name="delete", description="Command to delete messages")
async def delete(interaction: discord.Interaction, amount: int):
    required_role_id = 1261789230414172211

    if not any(role.id == required_role_id for role in interaction.user.roles):
        await interaction.response.send_message("You have access to this command!", ephemeral=True)
        return
    
    if interaction.user.guild_permissions.manage_messages:
        if 0 < amount <= 100:
            await interaction.response.defer(ephemeral=True)  # Defer the response to avoid timeout
            await interaction.channel.purge(limit=amount + 1)
            await interaction.followup.send(f"{amount} messages were deleted.", ephemeral=True)
        else:
            await interaction.response.send_message("The number of messages to delete must be between 1 and 100.", ephemeral=True)
    else:
        await interaction.response.send_message("You are not allowed to delete messages on this server.", ephemeral=True)

#suggestion command
@bot.command(name="suggestion", description="Command to send your suggestions")
async def suggestion(ctx, *, texto: str):
    if ctx.channel.id != 1290076086775844866:
        await ctx.message.delete()
        await ctx.send("This command can only be used on the allowed channel.", delete_after=5)
        return
    embed = discord.Embed(
        title="Suggestion",
        description=texto,
        color=discord.Color.yellow()
    )
    if isinstance(ctx.author, discord.Member):
        user = ctx.author
        embed.set_author(name=user.display_name)
        if user.avatar:
            embed.set_author(name=user.display_name, icon_url=user.avatar.url)
    await ctx.send(embed=embed)
    await ctx.message.delete()

if __name__ == "__main__":
    asyncio.run(main())
