import os
from dotenv import load_dotenv

load_dotenv()  # loads .env file

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

bot.run(TOKEN)
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os

# ------------------ BOT SETUP ------------------
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------ TICKET SYSTEM ------------------
@bot.tree.command(name="panel", description="Create a ticket panel (Admin only)")
@app_commands.describe(types="Optional comma-separated ticket types (e.g., Support, Report, Partnership)")
@app_commands.checks.has_permissions(administrator=True)
async def panel(interaction: discord.Interaction, types: str = None):
    ticket_types = ["General Support", "Report", "Partnership"]
    if types:
        ticket_types = [t.strip() for t in types.split(",")]

    embed = discord.Embed(
        title="🎫 Support Tickets",
        description="Select an option below to open a ticket!",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Our staff will assist you shortly.")

    view = TicketPanel(ticket_types)
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ Ticket panel created.", ephemeral=True)

class TicketPanel(discord.ui.View):
    def __init__(self, types):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown(types))

class TicketDropdown(discord.ui.Select):
    def __init__(self, types):
        options = [discord.SelectOption(label=t, description=f"Open a {t} ticket") for t in types]
        super().__init__(placeholder="Choose a ticket type...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")

        ticket_name = f"ticket-{interaction.user.name}".replace(" ", "-")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }

        channel = await guild.create_text_channel(
            ticket_name,
            overwrites=overwrites,
            category=category,
            topic=f"{interaction.user.id}|{self.values[0]}"
        )

        embed = discord.Embed(
            title=f"🎟 Ticket Opened - {self.values[0]}",
            description=f"Hello {interaction.user.mention}, please describe your issue.\nA staff member will be with you shortly.",
            color=discord.Color.green()
        )

        view = CloseButton()
        await channel.send(content=f"{interaction.user.mention} A ticket has been created.", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

        try:
            dm_embed = discord.Embed(
                title="🎫 Ticket Created",
                description=(
                    f"Thank you for creating a ticket, {interaction.user.mention}.\n\n"
                    f"Please be patient while our staff assist you.\n\n"
                    f"Your ticket channel: {channel.mention}\n"
                    f"Ticket type: {self.values[0]}"
                ),
                color=discord.Color.blue()
            )
            await interaction.user.send(embed=dm_embed)
        except discord.Forbidden:
            pass

class CloseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await close_ticket(interaction, reason=None)

@bot.tree.command(name="close", description="Close this ticket (optional reason)")
@app_commands.describe(reason="Reason for closing the ticket")
async def close(interaction: discord.Interaction, reason: str = None):
    await close_ticket(interaction, reason)

async def close_ticket(interaction: discord.Interaction, reason: str = None):
    if not interaction.channel.topic:
        await interaction.response.send_message("❌ This channel is not a ticket.", ephemeral=True)
        return

    try:
        owner_id, ticket_type = interaction.channel.topic.split("|")
        owner = interaction.guild.get_member(int(owner_id))
    except Exception:
        owner = None

    if owner:
        try:
            desc = f"Your ticket `{interaction.channel.name}` has been closed."
            if reason:
                desc += f"\nReason: {reason}"
            dm_embed = discord.Embed(title="🔒 Ticket Closed", description=desc, color=discord.Color.red())
            await owner.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    await interaction.response.send_message("❌ Closing ticket in 5 seconds...", ephemeral=True)
    await asyncio.sleep(5)
    await interaction.channel.delete()

# ------------------ STARTUP ------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ------------------ BOT TOKEN ------------------
# Token will be loaded from environment variable on Railway
bot.run(os.environ.get("DISCORD_BOT_TOKEN"))

