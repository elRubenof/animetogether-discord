import configparser
import requests
import discord
from discord.commands import option

import animeflv

configparser = configparser.ConfigParser()
configparser.read("config.ini")

config = configparser["CONFIG"]
lang = configparser[config["lang"]]

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(debug_guilds=[config["guild"]], intents=intents)

animes = []


@bot.event
async def on_ready():
    print(lang['on_ready_1'])


async def get_animes(ctx: discord.AutocompleteContext):
    lang['get_animes_1']

    if not ctx.value:
        return []

    results = animeflv.get_search(ctx.value)
    titles = (o.title for o in results)

    print(f"{lang['get_animes_2']}: {ctx.value}")
    print(f"└{lang['get_animes_3']}: {len(results)}")

    animes.clear()
    animes.extend(results)

    return titles


class MyView(discord.ui.View):
    bot
    anime: animeflv.Anime

    def __init__(self, bot, anime, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.anime = anime

    @discord.ui.button(label=f"{lang['myview_1']}  📺", style=discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        episode_select = await interaction.response.send_message(
            f"{lang['myview_2']} (1 - {len(self.anime.episodes)})"
        )
        selected_episode = 0

        try:
            response = await self.bot.wait_for(
                "message", check=lambda m: m.author == interaction.user, timeout=30.0
            )

            selected_episode = response.content
            await response.delete()
        except:
            await episode_select.edit_original_response(
                content=lang['myview_3']
            )
            return

        try:
            parsed_episode = int(selected_episode)
            if parsed_episode < 1 or parsed_episode > len(self.anime.episodes):
                raise Exception()
        except:
            await episode_select.edit_original_response(
                content=lang['myview_4']
            )
            return

        try:
            await episode_select.edit_original_response(content=lang['myview_5'])

            episode = ""
            for item in self.anime.episodes:
                if str(item.number) == selected_episode:
                    episode = item
                    break

            jimov_link = animeflv.get_jimov_link(episode.id_)
            link = get_ott_link(jimov_link)

            await episode_select.delete_original_response()
            await interaction.followup.send(
                f"[{self.anime.title} - {selected_episode}](<{link}>)"
            )
        except:
            await episode_select.edit_original_response(
                content=lang['myview_6']
            )
            return


def get_ott_link(url: str):
    api = "https://opentogethertube.com"

    token_response = requests.get(f"{api}/api/auth/grant")
    token = token_response.json()["token"]

    generate_response = requests.post(
        f"{api}/api/room/generate", headers={"Authorization": f"Bearer {token}"}
    )
    name = generate_response.json()["room"]

    played_video = requests.post(
        f"{api}/api/room/{name}/queue",
        json={"url": url},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    print(f"{api}/api/room/{name}/queue")
    print(f"url: {url}")

    print(played_video.json())

    return f"{api}/room/{name}"


@bot.slash_command()
@option("nombre", description=lang['search_1'], autocomplete=get_animes)
async def search(ctx: discord.ApplicationContext, nombre: str):
    lang['search_2']

    anime = None
    for item in animes:
        if item.title == nombre:
            anime = item
            break

    anime.set_info()

    embed = discord.Embed(
        colour=0x00FF00,
        title=anime.title,
    )

    embed.set_image(url=anime.image)

    if anime.description:
        description = anime.description
        if len(anime.description) > 1024:
            description = anime.description[0:1021] + "..."
        embed.add_field(name="", value=description, inline=False)
        embed.add_field(name="", value="", inline=False)

    embed.add_field(name=f"📚 {lang['search_3']}", value=", ".join(anime.genres), inline=False)
    embed.add_field(name="", value="", inline=False)
    embed.add_field(
        name=f"📖 {lang['search_4']}",
        value=f"∙ {lang['search_5']}: {anime.type_}\n∙ {lang['search_6']}: {anime.status}\n∙ {lang['search_7']}: {len(anime.episodes)}",
    )
    embed.add_field(
        name=f"⭐️ {lang['search_8']}",
        value=f"∙ {lang['search_9']}: {anime.valoration}\n∙ {lang['search_10']}: {anime.votes}\n∙ {lang['search_11']}: {anime.follows}",
    )

    await ctx.respond(embed=embed, view=MyView(bot=bot, anime=anime))


bot.run(config["token"])
