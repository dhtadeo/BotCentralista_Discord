import discord
from discord.ext import commands
import markovify

class BotMentionReply(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot: return

        bot_mentioned = self.bot.user in message.mentions
        is_reply_to_bot = False
        
        if message.reference and message.reference.message_id:
            try:
                cached_msg = message.reference.cached_message
                if cached_msg and cached_msg.author == self.bot.user:
                    is_reply_to_bot = True
                elif not cached_msg:
                    replied_msg = await message.channel.fetch_message(message.reference.message_id)
                    if replied_msg.author == self.bot.user:
                        is_reply_to_bot = True
            except Exception:
                pass 

        if not (bot_mentioned or is_reply_to_bot):
            return

        async with message.channel.typing():
            data = getattr(self.bot, 'global_chat_data', [])
            final_sentence = None

            def try_generate(list_of_messages):
                text = "\n".join(list_of_messages)
                if not text.strip() or len(text.splitlines()) < 5:
                    return None
                try:
                    model = markovify.NewlineText(text, well_formed=False)
                    for _ in range(50):
                        sentence = model.make_sentence()
                        if sentence: return sentence
                except:
                    pass
                return None

            if data:
                channel_msgs = []
                server_msgs = []

                for msg in data:
                    if message.guild and msg.get("server_id") == message.guild.id:
                        # From this server
                        text_msg = msg.get("content", "").strip()
                        attachments = msg.get("attachments", [])
                        if text_msg or attachments:
                            line = text_msg
                            if attachments: line += " " + " ".join(attachments)
                            line = line.strip()
                            
                            server_msgs.append(line)
                            # From this channel
                            if msg.get("channel_id") == message.channel.id:
                                channel_msgs.append(line)
                    
                    elif not message.guild and msg.get("channel_id") == message.channel.id:
                        # If DM
                        text_msg = msg.get("content", "").strip()
                        attachments = msg.get("attachments", [])
                        if text_msg or attachments:
                            line = text_msg
                            if attachments: line += " " + " ".join(attachments)
                            channel_msgs.append(line.strip())

                # LEVEL 1: Channel messages
                final_sentence = try_generate(channel_msgs)

                # LEVEL 2: Server messages
                if not final_sentence and message.guild:
                    final_sentence = try_generate(server_msgs)
            
            if final_sentence:
                try:
                    await message.reply(
                        final_sentence, 
                        allowed_mentions=discord.AllowedMentions.none()
                    )
                except Exception as e:
                    print(f"[Autoreply] ❌ Autoreply error: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(BotMentionReply(bot))