# Discord UI helper functions to create interactive menus
# Copyright (C) 2024 adversarial

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# import make_**** and use it inside of an app command interaction as the first response
import discord

# Every time a discord.Message is edited, the Select values are reset to default, and persist across dialogs.
# DiscordSmartSelect solves that by making a copy of the SelectOption list for each message
# It also unlocks the submit button only when the dialog is filled out and disables fields afterwards

# parent should be a discord.ui.View subclass with a method ".is_done()" that returns true if all fields are filled
# then, the control is disabled.
class DiscordSmartSelect(discord.ui.Select):
    def __init__(self, parent, **kwargs):
        self.option_copy = [ discord.SelectOption(label = o.label, value = o.value) for o in kwargs['options'] ]
        kwargs['options'] = self.option_copy
        super().__init__(**kwargs)
        
        self.parent = parent
        self.selected_action = None

    def is_done(self):
        return self.selected_action is not None

    def get_selected_value(self):
        return self.selected_action.value if self.is_done() else None
    
    def get_selected_label(self):
        return self.selected_action.label if self.is_done() else None

    def clear_defaults(self):
        for o in self.options:
            o.default = False

    async def callback(self, interaction:discord.Interaction):
        await interaction.response.defer()
        self.clear_defaults()
        self.selected_action = next(filter(lambda p: p.value == self.values[0], self.options), self.options[0])
        self.selected_action.default = True
        await self.parent.is_done()

class DiscordSmartTextInput(discord.ui.TextInput):
    def __init__(self, parent, **kwargs):
        super().__init__(**kwargs)

        self.parent = parent
        self.text = None

    def is_done(self):
        return self.text is not None

    def get_text(self):
        return self.text

    def clear_defaults(self):
        self.default = None

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.clear_defaults()
        self.default = self.value
        self.text = self.value
        await self.parent.is_done()

# User, action, option selector
# Generates a dialog like:
#
# ------------------------------
# |   TITLE                    |
# |   description goes here    |
# ------------------------------
# |  Select a user          v  |
# ------------------------------
# |  Select an action       v  |
# ------------------------------
# |  Select an option       v  |
# ------------------------------
#  __________   __________
# |  Submit  | |  Cancel  |
#  ¯¯¯¯¯¯¯¯¯¯   ¯¯¯¯¯¯¯¯¯¯ 
class SmartUserActionOptionView(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, 
                 action_placeholder: str = None, actions: list[discord.SelectOption] = None, 
                 option_placeholder: str = None, options: list[discord.SelectOption] = None,
                 timeout = 180):
        super().__init__(timeout = timeout)
        self.msg = None
        self.target = None
        self.cancelled = False
    
        self.actionselector = DiscordSmartSelect(parent = self, placeholder = action_placeholder, options = actions, row = 1)
        self.optionselector = DiscordSmartSelect(parent = self, placeholder = option_placeholder, options = options, row = 2)

        self.add_item(self.actionselector)
        self.add_item(self.optionselector)

    def get_selected_user(self):
        return self.target

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder = 'Select a user.', row = 0)
    async def user_selected(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await interaction.response.defer()
        self.target = select.values[0]
        select.placeholder = self.target.display_name
        await self.is_done()
    
    @discord.ui.button(label = 'Submit', disabled = True, row = 3)
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_elements()
        self.stop()
    
    @discord.ui.button(label = 'Cancel', disabled = False, row = 3)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_elements()
        self.cancelled = True
        self.stop()

    async def disable_elements(self):
        self.user_selected.disabled = True
        self.actionselector.disabled = True
        self.optionselector.disabled = True
        self.submit_button.disabled = True
        self.cancel_button.disabled = True
        await self.msg.edit(view = self)

    async def is_done(self):
        if (self.actionselector.is_done() and self.optionselector.is_done() and self.target) or (self.target and self.optionselector.get_selected_label() == 'Remove'):
            self.submit_button.disabled = False
            await self.msg.edit(view = self)

    def was_cancelled(self):
        return self.cancelled

# Put this in an app_command
# Returns (user: discord.User | discord.Member, action: discord.SelectOption, option: discord.SelectOption)
async def make_UserActionOptionPrompt(interaction: discord.Interaction, 
                           title: str = None, description: str = None,
                           action_placeholder: str = 'Select an action', actions: list[discord.SelectOption] = None, 
                           option_placeholder: str = 'Select an option', options: list[discord.SelectOption] = None,
                           **kwargs):
    dialog = SmartUserActionOptionView(interaction.user, action_placeholder = action_placeholder, actions = actions, option_placeholder = option_placeholder, options = options, **kwargs)
    await interaction.response.send_message(embed = discord.Embed(title = title, description = description), view = dialog, ephemeral = True)
    dialog.msg = await interaction.original_response()

    if await dialog.wait(): # returns true on timeout, false on stop()
        await interaction.followup.send('Dialog timed out. Please try again.', ephemeral = True)
        await dialog.disable_elements()
    else:
        if dialog.was_cancelled():
            await interaction.delete_original_response()
            return (None, None, None)
        else:
            return (dialog.get_selected_user(), 
                    discord.SelectOption(label = dialog.actionselector.get_selected_label(), value = dialog.actionselector.get_selected_value()), 
                    discord.SelectOption(label = dialog.optionselector.get_selected_label(), value = dialog.optionselector.get_selected_value()))

# Option and user selector
# Generates a dialog like:
#
# ------------------------------
# |   TITLE                    |
# |   description goes here    |
# ------------------------------
# ------------------------------
# |  Select an option       v  |
# ------------------------------
# |  Select a user          v  |
# ------------------------------
#  __________   __________
# |  Submit  | |  Cancel  |
#  ¯¯¯¯¯¯¯¯¯¯   ¯¯¯¯¯¯¯¯¯¯ 
class SmartOptionUserView(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, 
                 option_placeholder: str = None, options: list[discord.SelectOption] = None,
                 timeout = 180):
        super().__init__(timeout = timeout)
        self.msg = None
        self.target = None
        self.cancelled = False
    
        self.optionselector = DiscordSmartSelect(parent = self, placeholder = option_placeholder, options = options, row = 0)

        self.add_item(self.optionselector)

    def get_selected_user(self):
        return self.target

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder = 'Select a user.', row = 1)
    async def user_selected(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await interaction.response.defer()
        self.target = select.values[0]
        select.placeholder = self.target.display_name
        await self.is_done()
    
    @discord.ui.button(label = 'Submit', disabled = True, row = 2)
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_elements()
        self.stop()
    
    @discord.ui.button(label = 'Cancel', disabled = False, row = 2)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_elements()
        self.cancelled = True
        self.stop()

    async def disable_elements(self):
        self.user_selected.disabled = True
        self.optionselector.disabled = True
        self.submit_button.disabled = True
        self.cancel_button.disabled = True
        await self.msg.edit(view = self)

    async def is_done(self):
        if (self.optionselector.is_done() and self.target):
            self.submit_button.disabled = False
            await self.msg.edit(view = self)

    def was_cancelled(self):
        return self.cancelled

# Put this in an app_command
# Returns (user: discord.User | discord.Member, action: discord.SelectOption, option: discord.SelectOption)
async def make_OptionUserPrompt(interaction: discord.Interaction, 
                           title: str = None, description: str = None,
                           action_placeholder: str = 'Select an action', actions: list[discord.SelectOption] = None, 
                           option_placeholder: str = 'Select an option', options: list[discord.SelectOption] = None,
                           **kwargs):
    dialog = SmartOptionUserView(interaction.user, action_placeholder = action_placeholder, actions = actions, option_placeholder = option_placeholder, options = options, **kwargs)
    await interaction.response.send_message(embed = discord.Embed(title = title, description = description), view = dialog, ephemeral = True)
    dialog.msg = await interaction.original_response()

    if await dialog.wait(): # returns true on timeout, false on stop()
        await interaction.followup.send('Dialog timed out. Please try again.', ephemeral = True)
        await dialog.disable_elements()
    else:
        if dialog.was_cancelled():
            await interaction.delete_original_response()
            return (None, None)
        else:
            return (discord.SelectOption(label = dialog.optionselector.get_selected_label(), value = dialog.optionselector.get_selected_value()),
                    dialog.get_selected_user())

# Action and option selector
# Generates a dialog like:
#
# ------------------------------
# |   TITLE                    |
# |   description goes here    |
# ------------------------------
# |  Select an action       v  |
# ------------------------------
# |  Select an option       v  |
# ------------------------------
#  __________   __________
# |  Submit  | |  Cancel  |
#  ¯¯¯¯¯¯¯¯¯¯   ¯¯¯¯¯¯¯¯¯¯ 
class SmartActionOptionView(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, 
                 action_placeholder: str = None, actions: list[discord.SelectOption] = None, 
                 option_placeholder: str = None, options: list[discord.SelectOption] = None,
                 timeout = 180):
        super().__init__(timeout = timeout)
        self.msg = None
        self.cancelled = False
        
        self.actionselector = DiscordSmartSelect(parent = self, placeholder = action_placeholder, options = actions, row = 0)
        self.optionselector = DiscordSmartSelect(parent = self, placeholder = option_placeholder, options = options, row = 1)
        self.add_item(self.actionselector)
        self.add_item(self.optionselector)

    @discord.ui.button(label = 'Submit', disabled = True, row = 2)
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_elements()
        self.stop()

    @discord.ui.button(label = 'Cancel', disabled = False, row = 2)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_elements()
        self.cancelled = True
        self.stop()

    async def disable_elements(self):
        self.actionselector.disabled = True
        self.optionselector.disabled = True
        self.submit_button.disabled = True
        self.cancel_button.disabled = True
        await self.msg.edit(view = self)

    async def is_done(self):
        if self.actionselector.is_done() and self.optionselector.is_done():
            self.submit_button.disabled = False
            await self.msg.edit(view = self)

    def was_cancelled(self):
        return self.cancelled
    
# Put this in an app_command
# Returns (action: discord.SelectOption, option: discord.SelectOption)
async def make_ActionOptionPrompt(interaction: discord.Interaction, 
                           title: str = None, description: str = None,
                           action_placeholder: str = 'Select an action', actions: list[discord.SelectOption] = None, 
                           option_placeholder: str = 'Select an option', options: list[discord.SelectOption] = None,
                           **kwargs):
    dialog = SmartActionOptionView(interaction.user, action_placeholder = action_placeholder, actions = actions, option_placeholder = option_placeholder, options = options, **kwargs)
    await interaction.response.send_message(embed = discord.Embed(title = title, description = description), view = dialog, ephemeral = True)
    dialog.msg = await interaction.original_response()

    if await dialog.wait(): # returns true on timeout, false on stop()
        await interaction.followup.send('Dialog timed out. Please try again.', ephemeral = True)
        await dialog.disable_elements()
    else:
        if dialog.was_cancelled():
            await interaction.delete_original_response()
            return (None, None)
        else:
            return (discord.SelectOption(label = dialog.actionselector.get_selected_label(), value = dialog.actionselector.get_selected_value()), 
                    discord.SelectOption(label = dialog.optionselector.get_selected_label(), value = dialog.optionselector.get_selected_value()))

# Option Selector
# Generates a dialog like:
#
# ------------------------------
# |   TITLE                    |
# |   description goes here    |
# ------------------------------
# |  Select an option       v  |
# ------------------------------
#  __________   __________
# |  Submit  | |  Cancel  |
#  ¯¯¯¯¯¯¯¯¯¯   ¯¯¯¯¯¯¯¯¯¯ 
class SmartOptionView(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, 
                 option_placeholder: str = None, options: list[discord.SelectOption] = None,
                 timeout = 180):
        super().__init__(timeout = timeout)
        self.msg = None
        self.cancelled = False
        
        self.optionselector = DiscordSmartSelect(parent = self, placeholder = option_placeholder, options = options, row = 0)
        self.add_item(self.optionselector)

    @discord.ui.button(label = 'Submit', disabled = True, row = 1)
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_elements()
        self.stop()

    @discord.ui.button(label = 'Cancel', disabled = False, row = 1)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_elements()
        self.cancelled = True
        self.stop()

    async def disable_elements(self):
        self.optionselector.disabled = True
        self.submit_button.disabled = True
        self.cancel_button.disabled = True
        await self.msg.edit(view = self)

    async def is_done(self):
        if self.optionselector.is_done():
            self.submit_button.disabled = False
            await self.msg.edit(view = self)

    def was_cancelled(self):
        return self.cancelled
    
# Put this in an app_command
# Returns option: discord.SelectOption
async def make_OptionPrompt(interaction: discord.Interaction, 
                           title: str = None, description: str = None,
                           option_placeholder: str = 'Select an option', options: list[discord.SelectOption] = None,
                           **kwargs):
    dialog = SmartOptionView(interaction.user, option_placeholder = option_placeholder, options = options, **kwargs)
    await interaction.response.send_message(embed = discord.Embed(title = title, description = description), view = dialog, ephemeral = True)
    dialog.msg = await interaction.original_response()

    if await dialog.wait(): # returns true on timeout, false on stop()
        await interaction.followup.send('Dialog timed out. Please try again.', ephemeral = True)
        await dialog.disable_elements()
    else:
        if dialog.was_cancelled():
            await interaction.delete_original_response()
            return None
        else:
            return discord.SelectOption(label = dialog.optionselector.get_selected_label(), value = dialog.optionselector.get_selected_value())
   
# Option Selector (no submit button)
# Generates a dialog like:
#
# ------------------------------
# |   TITLE                    |
# |   description goes here    |
# ------------------------------
# |  Select an option       v  |
# ------------------------------
#  __________
# |  Cancel  |
#  ¯¯¯¯¯¯¯¯¯¯ 
class SmartOptionViewNoSubmit(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, 
                 option_placeholder: str = None, options: list[discord.SelectOption] = None,
                 timeout = 180):
        super().__init__(timeout = timeout)
        self.msg = None
        self.cancelled = False
        
        self.optionselector = DiscordSmartSelect(parent = self, placeholder = option_placeholder, options = options, row = 0)
        self.add_item(self.optionselector)

    @discord.ui.button(label = 'Cancel', disabled = False, row = 1)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_elements()
        self.cancelled = True
        self.stop()

    async def disable_elements(self):
        self.optionselector.disabled = True
        self.cancel_button.disabled = True
        await self.msg.edit(view = self)

    async def is_done(self):
        if self.optionselector.is_done():
            await self.disable_elements()
            self.stop()

    def was_cancelled(self):
        return self.cancelled
    
# Put this in an app_command
# Returns option: discord.SelectOption
async def make_OptionPromptNoSubmit(interaction: discord.Interaction, 
                           title: str = None, description: str = None,
                           option_placeholder: str = 'Select an option', options: list[discord.SelectOption] = None,
                           **kwargs):
    dialog = SmartOptionViewNoSubmit(interaction.user, option_placeholder = option_placeholder, options = options, **kwargs)
    await interaction.response.send_message(embed = discord.Embed(title = title, description = description), view = dialog, ephemeral = True)
    dialog.msg = await interaction.original_response()

    if await dialog.wait(): # returns true on timeout, false on stop()
        await interaction.followup.send('Dialog timed out. Please try again.', ephemeral = True)
        await dialog.disable_elements()
    else:
        if dialog.was_cancelled():
            await interaction.delete_original_response()
            return None
        else:
            return discord.SelectOption(label = dialog.optionselector.get_selected_label(), value = dialog.optionselector.get_selected_value())

# Option Selector Then Modal
# Generates a dialog like:
#
# ------------------------------
# |   TITLE                    |
# |   description goes here    |
# ------------------------------
# |  Select an option       v  |
# ------------------------------
#  __________   __________
# |  Submit  | |  Cancel  |
#  ¯¯¯¯¯¯¯¯¯¯   ¯¯¯¯¯¯¯¯¯¯ 
# then a modal for text input
# ------------------------------
# |   TITLE                    |
# |   description goes here    |
# |                            |
# |  [                     ]   |
# |                            |
# |                 [ Submit ] |
# ------------------------------

class DiscordTextModal(discord.ui.Modal):
    def __init__(self, parent, modal_label, modal_default, **kwargs):
        super().__init__(**kwargs)
        self.parent = parent
        self.input = discord.ui.TextInput(label = modal_label, style = discord.TextStyle.short, default = modal_default)
        self.text = None
        self.add_item(self.input)

    def get_input(self):
        return self.text

    def is_done(self):
        return self.text is not None
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.text = self.input.value
        await self.parent.is_done()

class DiscordSmartSelectThenModal(DiscordSmartSelect):
    def __init__(self, parent, modal, trigger_option = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.file_input = None
        self.modal = modal
        self.trigger_option = trigger_option

    async def callback(self, interaction:discord.Interaction):
        self.clear_defaults()
        self.selected_action = next(filter(lambda p: p.value == self.values[0], self.options), self.options[0])
        self.selected_action.default = True
        if (not self.trigger_option
        or self.selected_action.label.lower() == self.trigger_option.label.lower()):
            await interaction.response.send_modal(self.modal)
            if await self.modal.wait():
                self.parent.cancelled = True
            else:
                self.clear_defaults()
                self.placeholder = self.modal.get_input()
                await self.parent.msg.edit(view = self.parent)
        else:
            await interaction.response.defer()
        await self.parent.is_done()

class SmartOptionViewThenModal(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, 
                 modal_title: str, modal_input_label: str, modal_default: str, 
                 option_placeholder: str = None, options: list[discord.SelectOption] = None,
                 trigger_option: discord.SelectOption = None,
                 timeout = 180):
        super().__init__(timeout = timeout)
        self.modal_title = modal_title
        self.modal_input_label = modal_input_label
        self.modal_default = modal_default
        self.msg = None
        self.cancelled = False

        self.text_input = DiscordTextModal(title = self.modal_title, 
                                           parent = self, 
                                           modal_label = self.modal_input_label, 
                                           modal_default = self.modal_default)
        
        self.optionselector = DiscordSmartSelectThenModal(parent = self, modal = self.text_input, trigger_option = trigger_option, placeholder = option_placeholder, options = options, row = 0)
        self.add_item(self.optionselector)
    
    @discord.ui.button(label = 'Cancel', disabled = False, row = 1)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_elements()
        self.cancelled = True
        self.stop()

    def get_text_input(self):
        return self.text_input.get_input()
    
    async def disable_elements(self):
        self.optionselector.disabled = True
        self.cancel_button.disabled = True
        await self.msg.edit(view = self)
    
    async def is_done(self):
        if self.optionselector.is_done() and self.text_input.is_done():
            await self.disable_elements()
            self.stop()

    def was_cancelled(self):
        return self.cancelled
    
# Put this in an app_command
# Returns input str
async def make_OptionPromptThenModal(interaction: discord.Interaction, 
                           title: str = None, description: str = None,
                           modal_title: str = None, modal_input_label = None, modal_default = None,
                           option_placeholder: str = 'Select an option', options: list[discord.SelectOption] = None,
                           **kwargs):
    dialog = SmartOptionViewThenModal(interaction.user, 
                                      modal_title = modal_title, modal_input_label = modal_input_label, modal_default = modal_default,
                                      option_placeholder = option_placeholder, options = options, 
                                      **kwargs)
    await interaction.response.send_message(embed = discord.Embed(title = title, description = description), view = dialog, ephemeral = True)
    dialog.msg = await interaction.original_response()

    if await dialog.wait(): # returns true on timeout, false on stop()
        await interaction.followup.send('Dialog timed out. Please try again.', ephemeral = True)
        await dialog.disable_elements()
    else:
        if dialog.was_cancelled():
            await interaction.delete_original_response()
            return None
        else:
            return (discord.SelectOption(label = dialog.optionselector.get_selected_label(), value = dialog.optionselector.get_selected_value()),
                    dialog.get_text_input())

# User, Action, Option Selector then Modal
# Generates a dialog like:
#
# ------------------------------
# |   TITLE                    |
# |   description goes here    |
# ------------------------------
# |  Select a user          v  |
# ------------------------------
# |  Select an action       v  |
# ------------------------------
# |  Select an option       v  |
# ------------------------------
#  __________   __________
# |  Submit  | |  Cancel  |
#  ¯¯¯¯¯¯¯¯¯¯   ¯¯¯¯¯¯¯¯¯¯ 

# then a modal for text input
# ------------------------------
# |   TITLE                    |
# |   description goes here    |
# |                            |
# |  [                     ]   |
# |                            |
# |                 [ Submit ] |
# ------------------------------
class SmartUserActionOptionViewThenModal(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, 
                 action_placeholder: str = None, actions: list[discord.SelectOption] = None, 
                 option_placeholder: str = None, options: list[discord.SelectOption] = None,
                 modal_title: str = None, modal_input_label = None, modal_default = None,
                 trigger_option: discord.SelectOption = None,
                 timeout = 180):
        super().__init__(timeout = timeout)
        self.msg = None
        self.target = None
        self.cancelled = False

        self.modal_title = modal_title
        self.modal_input_label = modal_input_label
        self.modal_default = modal_default
        self.msg = None
        self.cancelled = False

        self.text_input = DiscordTextModal(title = self.modal_title, 
                                           parent = self, 
                                           modal_label = self.modal_input_label, 
                                           modal_default = self.modal_default)
        
        self.actionselector = DiscordSmartSelectThenModal(parent = self, modal = self.text_input, trigger_option = trigger_option, placeholder = action_placeholder, options = actions, row = 1)
        self.optionselector = DiscordSmartSelect(parent = self, placeholder = option_placeholder, options = options, row = 2)

        self.add_item(self.actionselector)
        self.add_item(self.optionselector)

    def get_text_input(self):
        return self.text_input.get_input()

    def get_selected_user(self):
        return self.target

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder = 'Select a user.', row = 0)
    async def user_selected(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        await interaction.response.defer()
        self.target = select.values[0]
        select.placeholder = self.target.display_name
        await self.is_done()
    
    @discord.ui.button(label = 'Submit', disabled = True, row = 3)
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_elements()
        #if self.actionselector.is_done() and self.actionselector.get_selected_label().lower() == 'custom':
        #    await interaction.response.send_modal(self.text_input)
        #    if await self.text_input.wait():
        #        self.cancelled = True
        #else:
        #    await interaction.response.defer()
        self.stop()
    
    @discord.ui.button(label = 'Cancel', disabled = False, row = 3)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_elements()
        self.cancelled = True
        self.stop()

    async def disable_elements(self):
        self.user_selected.disabled = True
        self.actionselector.disabled = True
        self.optionselector.disabled = True
        self.submit_button.disabled = True
        self.cancel_button.disabled = True
        await self.msg.edit(view = self)

    async def is_done(self):
        if ((self.actionselector.is_done() and self.optionselector.is_done() and self.target) 
        or (self.target and self.optionselector.get_selected_label() == 'Remove')):
            self.submit_button.disabled = False
            await self.msg.edit(view = self)

    def was_cancelled(self):
        return self.cancelled

# Put this in an app_command
# Returns (user: discord.User | discord.Member, action: discord.SelectOption, option: discord.SelectOption)
async def make_UserActionOptionPromptThenModal(interaction: discord.Interaction, 
                           title: str = None, description: str = None,
                           action_placeholder: str = 'Select an action', actions: list[discord.SelectOption] = None, 
                           option_placeholder: str = 'Select an option', options: list[discord.SelectOption] = None,
                           modal_title: str = None, modal_input_label = None, modal_default = None,
                           trigger_option: discord.SelectOption = None,
                           **kwargs):
    dialog = SmartUserActionOptionViewThenModal(interaction.user, 
                                       action_placeholder = action_placeholder, actions = actions, 
                                       option_placeholder = option_placeholder, options = options,              
                                       modal_title = modal_title, modal_input_label = modal_input_label, modal_default = modal_default,
                                       trigger_option = trigger_option,
                                       **kwargs)
    await interaction.response.send_message(embed = discord.Embed(title = title, description = description), view = dialog, ephemeral = True)
    dialog.msg = await interaction.original_response()

    if await dialog.wait(): # returns true on timeout, false on stop()
        await interaction.followup.send('Dialog timed out. Please try again.', ephemeral = True)
        await dialog.disable_elements()
    else:
        if dialog.was_cancelled():
            await interaction.delete_original_response()
            return (None, None, None, None)
        else:
            return (dialog.get_selected_user(), 
                    discord.SelectOption(label = dialog.actionselector.get_selected_label(), value = dialog.actionselector.get_selected_value()), 
                    discord.SelectOption(label = dialog.optionselector.get_selected_label(), value = dialog.optionselector.get_selected_value()),
                    dialog.get_text_input())