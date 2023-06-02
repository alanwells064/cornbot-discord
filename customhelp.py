# sublcass of discord.ext.commands.HelpCommand
# allows for a custom help command (obviously)
# I used this as a template: https://www.pythondiscord.com/pages/guides/python-guides/discordpy_help_command/

import discord, helpstrings, util
from discord.ext import commands

class CustomHelp(commands.HelpCommand):

    async def send_bot_help(self, mapping):
        """
        This is triggered when !help is invoked.

        This example demonstrates how to list the commands that the member invoking the help command can run.
        """
        if isinstance(self.context.channel, discord.channel.DMChannel):
            # for registered users
            if self.context.author.id in util.registered_users:
                await self.context.send(helpstrings.HELP["help"])
            # for unregistered users
            else:
                await self.context.send(helpstrings.NOOB_HELP)

    async def send_command_help(self, command):
        """
        Command to view commands and help topics.
        Usable by unregistered users, but they see a limited command selection.
        """
        # registered users
        if isinstance(self.context.channel, discord.channel.DMChannel) and self.context.author.id in util.registered_users:
            # if arg matches a command, send help for that command
            if command.name in helpstrings.HELP:
                await self.context.send(helpstrings.HELP[command.name])
            # if arg doesn't match a command, send regular help string
            else:
                await self.context.send(helpstrings.HELP["help"])
        # unregistered users
        elif isinstance(self.context.channel, discord.channel.DMChannel):
            await self.context.send(helpstrings.NOOB_HELP)

    # async def send_group_help(self, group):
    #     """This is triggered when !help <group> is invoked."""
    #     await self.context.send("This is the help page for a group command")

    # async def send_cog_help(self, cog):
    #     """This is triggered when !help <cog> is invoked."""
    #     await self.context.send("This is the help page for a cog")

    # async def send_error_message(self, error):
    #     """If there is an error, send a embed containing the error."""
    #     channel = self.get_destination() # this defaults to the command context channel
    #     await channel.send(error)