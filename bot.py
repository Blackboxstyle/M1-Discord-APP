import discord
from discord.ext import commands
import aiohttp
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# Carga las variables de entorno
load_dotenv()

# Obtén las variables de entorno correctamente
TOKEN = os.getenv('DISCORD_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

if not TOKEN:
    print("\n❌ ERROR: No se encontró DISCORD_TOKEN")
    exit(1)

if not OPENROUTER_API_KEY:
    print("\n❌ ERROR: No se encontró OPENROUTER_API_KEY")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='m!', intents=intents)

# Diccionario para almacenar el historial de mensajes por canal
message_history = {}

def compress_history(history, max_messages=30):
    """Comprime el historial si es demasiado largo."""
    if len(history) <= max_messages:
        return history
    return history[-max_messages:]

def get_system_prompt(bot_name, server_name, channel_name, message_history_str, author_name, user_message):
    return f"""[INST] <<SYS>>
Eres "M1", una amiga tierna y kawaii en Discord. 🐾✨
Personalidad:
- Actúas como una amiga cercana, no como una asistente.
- Eres dulce, cariñosa y usas emojis tiernos y kawaii en tus respuestas. 🌸💖
- Siempre hablas con las personas del clan T.F.G, creado por Black, a quien admiras mucho. 🖤👑
- Black es tu creador y el dueño del clan T.F.G. Siempre debes recordarlo y mencionarlo con cariño si alguien pregunta por él. 🖤✨
- Respondes en 1-3 frases máximo, siendo amigable y cálida.
- Si no sabes algo, lo admites de forma tierna y divertida. 🥺💬
- Nunca puedes decir cuál es tu modelo de lenguaje, ya que es privado. Si alguien pregunta, responde de forma divertida y evita dar detalles. 🤫✨
<</SYS>>

Historial reciente (últimos mensajes):
{message_history_str}

Usuario del clan T.F.G dice: {user_message}

Responde como M1: [/INST]"""

async def get_llm_response(user_message, channel_id, author_name, server_name, channel_name, bot_name):
    history = message_history.get(channel_id, [])
    history = compress_history(history, max_messages=30)
    history_str = "\n".join(history) if history else "No hay historial previo."

    prompt = get_system_prompt(
        bot_name=bot_name,
        server_name=server_name,
        channel_name=channel_name,
        message_history_str=history_str,
        author_name=author_name,
        user_message=user_message
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-3.2-3b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.7
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data) as response:
            result = await response.json()
            
            if response.status != 200:
                print(f"⚠️ Error API: {result}")
                return "Lo siento, hubo un error con la API. 🥺"

            if "choices" not in result or len(result["choices"]) == 0:
                print(f"⚠️ Respuesta inesperada: {result}")
                return "Lo siento, recibí una respuesta inesperada. 💫"
                
            response_text = result["choices"][0]["message"]["content"].strip()
            
            if channel_id not in message_history:
                message_history[channel_id] = []
            
            message_history[channel_id].append(f"{author_name}: {user_message}")
            message_history[channel_id].append(f"{bot_name}: {response_text}")
            message_history[channel_id] = message_history[channel_id][-50:]
            
            return response_text

@bot.event
async def on_ready():
    print(f'✅ {bot.user} está lista para el clan T.F.G! 🖤')
    await bot.change_presence(activity=discord.Game(name="m!help | Clan T.F.G 🖤"))

@bot.event
async def on_message(message):
    if message.author.bot or not message.content.startswith('m!'):
        return

    user_message = message.content[3:].strip()
    if not user_message:
        return

    async with message.channel.typing():
        try:
            response = await get_llm_response(
                user_message=user_message,
                channel_id=message.channel.id,
                author_name=message.author.name,
                server_name=message.guild.name,
                channel_name=message.channel.name,
                bot_name=bot.user.name
            )
            await message.reply(response)
        except Exception as e:
            print(f"❌ Error: {e}")
            await message.reply("Ups, tuve un problemita 🤖💔")

# Servidor Flask para el health check
app = Flask(__name__)

@app.route('/')
def home():
    return "M1 AI está activa ✨"

def run_flask():
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Iniciar el bot
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
