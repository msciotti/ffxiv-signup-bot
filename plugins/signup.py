# coding=utf-8

import psycopg2

from disco.bot import Plugin
from disco.types.message import MessageTable


class SignupPlugin(Plugin):
    def load(self, ctx):
        self.database = psycopg2.connect("dbname=ffxiv_signup_bot")

    @Plugin.command(
        "config",
        "<admin_channel_id:snowflake> <signup_channel_id:snowflake> <announce_channel_id:snowflake>",
    )
    def on_config(
        self, event, admin_channel_id, signup_channel_id, announce_channel_id
    ):
        guild_id = event.msg.guild.id
        cursor = self.database.cursor()
        cursor.execute(
            "insert into guild_config values({}, {}, {}, {})".format(
                guild_id, admin_channel_id, signup_channel_id, announce_channel_id
            )
        )

        self.database.commit()
        event.msg.reply("Succesfully configured this Discord for use!")

    @Plugin.command(
        "create", "<name:str> <tanks:int> <healers:int> <dps:int> <message:str...>"
    )
    def on_create(self, event, name, tanks, healers, dps, message):
        cur = self.database.cursor()
        cur.execute(
            "select * from guild_config where guild_id = {}".format(event.msg.guild.id)
        )
        config = cur.fetchone()
        print config

        if config is None:
            event.msg.reply("I'm not configured! Please set up your channels first.")

        if event.msg.channel != config[1]:
            event.msg.reply("Sorry, that command can't be run from that channel")

        confirm_message = event.msg.reply(
            "You're creating an event named {} that requires {} tanks, {} healers, and {} dps. Your custom message is \n\n{}\n\nReact with <:greentick:326519582657609728> if correct.".format(
                name, tanks, healers, dps, message
            )
        )
        cur = self.database.cursor()
        cur.execute(
            "insert into events values(%s, %s, %s, %s, %s, %s, %s, %s)", (
                confirm_message.id, name, message, tanks, healers, dps, False, False
            )
        )
        self.database.commit()

    @Plugin.listen("MessageReactionAdd")
    def on_message_reaction_add(self, event):
        cur = self.database.cursor()
        cur.execute("select * from events where id = {}".format(event.message_id))
        e = cur.fetchone()
        if e is None:
            return

        if event.emoji.id == 326519582657609728:
            cur.execute(
                "update events set confirmed = true where events.id = {}".format(e[0])
            )
            self.database.commit()
            admin_channel = self.client.api.channels_get(event.channel_id)
            admin_channel.send_message(
                "Event confirmed! React with <:cheer:612778926640726024> to announce it to your announcement channel."
            )
            return

        if event.emoji.id == 612778926640726024 and e[6] is True and e[7] is False:
            admin_channel = self.client.api.channels_get(event.channel_id)

            admin_channel.send_message("Announcing your event!")
            cur.execute(
                "select announce_channel_id from guild_config where admin_channel_id = {}".format(
                    event.channel_id
                )
            )
            channel_id = cur.fetchone()[0]

            announce_channel = self.client.api.channels_get(channel_id)
            announce_channel.send_message("{} - {}".format(e[1], e[2]))
            cur.execute(
                "update events set announced = true where events.id = {}".format(e.id)
            )
            self.database.commit()

