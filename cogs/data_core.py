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
        
        # Variables Globales en la RAM
        self.bot.global_chat_data = []      # Para búsquedas rápidas, WordClouds y canales
        self.bot.global_markov_model = None # Para el modelo unificado

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
                print("⚠️ [Data Core] No se encontró chat_log.json.")
                return

            with open(self.log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if data:
                # 1. Guardamos los datos puros en RAM
                self.bot.global_chat_data = data
                
                # 2. Entrenamos a Markovify
                texto = self._extract_text_for_markovify(data)
                if texto.strip() and len(texto.splitlines()) >= 5:
                    self.bot.global_markov_model = markovify.NewlineText(texto, well_formed=False)
                    print(f"🧠 [Data Core] Cerebro en línea. {len(data)} mensajes en memoria global.")
                    
        except Exception as e:
            print(f"❌ [Data Core] Error al actualizar el cerebro: {e}")

    @update_brain_loop.before_loop
    async def before_update_brain(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(DataCore(bot))