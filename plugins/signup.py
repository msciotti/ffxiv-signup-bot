from disco.bot import Plugin
from disco.types.message import MessageTable
from sqlitedict import SqliteDict


# Unused
JOB_EMOJIS = [
    "pld:612795608083988480",
    "war:612798409589391390",
    "drk:612795608192778291",
    "gnb:612795608217944064",
    "whm:612798823349354537",
    "sch:612795608171937801",
    "ast:612795607903371264",
    "mnk:612795607987519558",
    "drg:612795608159354894",
    "nin:612795608050171938",
    "sam:612795608092377088",
    "mch:612795608453087245",
    "brd:612795608239046707",
    "dnc:612795607756832774",
    "blm:612795608029462528",
    "smn:612798846803902465",
    "rdm:612795607811358721",
]

ROLE_EMOJIS = [
    "tank:614600978930335757",
    "healer:614601235638779904",
    "melee:614601235583991809",
    "ranged:614601235261161474",
    "magic:614601235651362836",
]

def confirm_event(self, guild_id, admin_channel, message_id):
    data = self.signups[guild_id]
    data[message_id]["confirmed"] = True
    self.signups[guild_id] = data

    event_message = self.client.api.channels_messages_get(
        admin_channel.id, message_id
    )
    admin_channel.send_message(
        "Event confirmed! React again with the cheer to announce it to your announcement channel."
    )
    event_message.add_reaction("cheer:612778926640726024")

def announce_event(self, guild_id, admin_channel, message_id):
    admin_channel.send_message("Announcing your event!")

    announce_channel_id = self.guild_configs[guild_id]["announce_channel_id"]
    announce_channel = self.client.api.channels_get(announce_channel_id)
    announcement = announce_channel.send_message(
        "{} - {}\n\n React to this message to sign up!".format(
            self.signups[guild_id][message_id]["name"], self.signups[guild_id][message_id]["message"]
        )
    )

    data = self.signups[guild_id]
    data[message_id]["announced"] = True
    self.signups[guild_id] = data

    for emoji in ROLE_EMOJIS:
        announcement.add_reaction(emoji)

class SignupPlugin(Plugin):
    def load(self, ctx):
      self.guild_configs = SqliteDict('./guild_configs.sqlite', autocommit=True)
      self.signups = SqliteDict('./signups.sqlite', autocommit=True)

    def unload(self, ctx):
        self.guild_configs.close()
        self.signups.close()

    @Plugin.command(
        "config",
        "<admin_channel_id:snowflake> <signup_channel_id:snowflake> <announce_channel_id:snowflake>",
    )
    def on_config(
        self, event, admin_channel_id, signup_channel_id, announce_channel_id
    ):
        guild_id = str(event.msg.guild.id)
        self.guild_configs[guild_id] = {
            "admin_channel_id": admin_channel_id,
            "signup_channel_id": signup_channel_id,
            "announce_channel_id": announce_channel_id,
        }
        event.msg.reply("Succesfully configured this Discord for use!")

    @Plugin.command(
        "create", "<name:str> <tanks:int> <healers:int> <dps:int> <message:str...>"
    )
    def on_create(self, event, name, tanks, healers, dps, message):
        guild_id = str(event.msg.guild.id)
        config = self.guild_configs[guild_id]

        if config is None:
            event.msg.reply("I'm not configured! Please set up your channels first.")

        confirm_message = event.msg.reply(
            "You're creating an event named {} that requires {} tanks, {} healers, and {} dps. Your custom message is \n\n{}\n\nReact to confirm.".format(
                name, tanks, healers, dps, message
            )
        )

        confirm_message.add_reaction("greentick:612799716161486888")

        self.signups[guild_id] = {
          str(confirm_message.id): {
            "name": name,
            "message": message,
            "tanks": tanks,
            "healers": healers,
            "dps": dps,
            "confirmed": False,
            "announced": False,
          }
        }

        print self.signups

    @Plugin.listen("MessageReactionAdd")
    def on_message_reaction_add(self, event):
        # Not the bot
        if event.user_id == 612451478485073925:
            return

        message_id = str(event.message_id)
        guild_id = str(event.guild.id)
        admin_channel_id = self.guild_configs[guild_id]["admin_channel_id"]
        admin_channel = self.client.api.channels_get(admin_channel_id)

        if self.signups[guild_id][message_id] is None:
          return

        if self.guild_configs[guild_id] is None:
            return

        # Green check emoji, not bot id
        if event.emoji.id == 612799716161486888:
            confirm_event(self, guild_id, admin_channel, message_id)

        # Cheer emoji, not bot id
        if event.emoji.id == 612778926640726024 and self.signups[guild_id][message_id]["confirmed"] is True:
            print 'here'
            announce_event(self, guild_id, admin_channel, message_id)


