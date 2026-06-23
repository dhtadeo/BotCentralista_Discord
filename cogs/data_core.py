import discord
from discord.ext import commands, tasks
import markovify
import os
import json

class DataCore(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(cog_dir)
        self.log_path = os.path.join(self.root_dir, "logs", "chat_log.json")
        
        self.bot.global_chat_data = []      # Faster searches
        self.bot.global_markov_model = None # Unified model

        self.update_brain_loop.start()

    def cog_unload(self):
        self.update_brain_loop.cancel()

    def _extract_text_for_markovify(self, data):
        mensajes = []
        for msg in data:
            texto_msg = msg.get("content", "").strip()
            adjuntos = msg.get("attachments", [])
            
            if texto_msg or adjuntos:
                linea = texto_msg
                if adjuntos:
                    linea += " " + " ".join(adjuntos)
                mensajes.append(linea.strip())
        return "\n".join(mensajes)

    @tasks.loop(minutes=30)
    async def update_brain_loop(self):
        try:
            if not os.path.exists(self.log_path):
                print("[Markovify] ⚠️ chat_log.json not found.")
                return

            with open(self.log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if data:
                self.bot.global_chat_data = data
                
                texto = self._extract_text_for_markovify(data)
                if texto.strip() and len(texto.splitlines()) >= 5:
                    self.bot.global_markov_model = markovify.NewlineText(texto, well_formed=False)
                    print(f"[Markovify] 🧠 The model is online. {len(data)} messages are loaded.")
                    
        except Exception as e:
            print(f"[Markovify] ❌ Error auto-updating the model: {e}")

    @update_brain_loop.before_loop
    async def before_update_brain(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(DataCore(bot))