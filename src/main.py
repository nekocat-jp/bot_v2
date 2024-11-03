import os
import re
import urllib.parse
import asyncio
import aiohttp
import discord
from discord.ui import Select, View
from discord import Interaction
from discord import app_commands
from PIL import Image
from utils.loader import load_config, check_key
from utils.error import error_exit
from utils.api import fetch
from utils.database import Database

config = load_config()
api_key = config.get('API_KEY')
token = config.get('TOKEN')
if api_key is None:
	error_exit("API_KEYが見つかりません")
if token is None:
	error_exit("TOKENが見つかりません")
check_key(api_key)

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print('起動しました')
    await tree.sync()

# stats select menu
class SelectView(View):
	@discord.ui.select(
		cls=Select,
		placeholder="アカウント選択"
	)
	async def selectMenu(self, interaction: Interaction, select: Select):
		await interaction.response.send_message(f"読み込んでいます", ephemeral=True)
		data = select.values[0].split(",")
		enc_puuid = urllib.parse.quote(data[1])
		url_acc = f"https://api.henrikdev.xyz/valorant/v2/by-puuid/account/{enc_puuid}?api_key={api_key}"
		url_mmr = f"https://api.henrikdev.xyz/valorant/v3/by-puuid/mmr/ap/pc/{enc_puuid}?api_key={api_key}"
		async with aiohttp.ClientSession() as session:
			acc_data = await fetch(session, url_acc)
			mmr_data = await fetch(session, url_mmr)
			if acc_data is None:
				await interaction.followup.send(f'情報を取得できませんでした。', ephemeral=True)
				return
			if mmr_data is None:
				await interaction.followup.send(f'情報を取得できませんでした。', ephemeral=True)
				return
		enc_acc_name = urllib.parse.quote(acc_data['data']['name'])
		enc_acc_tag = urllib.parse.quote(acc_data['data']['tag'])
		embed = discord.Embed(title=f'{acc_data['data']['name']}#{acc_data['data']['tag']}',
			url=f"https://tracker.gg/valorant/profile/riot/{enc_acc_name}%23{enc_acc_tag}/overview",
			description=f"current name: `{acc_data['data']['name']}#{acc_data['data']['tag']}` \n\nlevel: `{acc_data['data']['account_level']}`\ncurrent rank: `{mmr_data['data']['current']['tier']['name']} {mmr_data['data']['current']['rr']}rr`\npeak rank: `{mmr_data['data']['peak']['tier']['name']} ({mmr_data['data']['peak']['season']['short']})`\n\npuuid: `{enc_puuid}`\n** **",
			colour=0x00e4f5)
		embed.set_footer(text=f"by {interaction.user}")
		await interaction.followup.send(f"", embed=embed)

# stats command
@tree.command(name='stats')
async def status(interaction: discord.Interaction):
	view = SelectView()
	db = Database()
	data = db.get_data(interaction.user.id)
	if not data:
		await interaction.response.send_message(f"/registerコマンドでIDを登録してください。複数登録可能です。", ephemeral=True)
		return
	for username, puuid, memo in data:
		view.selectMenu.add_option(
			label=username,
			value=f"{username},{puuid},{memo}",
			description=memo,
		)
	db.close_connection()
	await interaction.response.send_message("statsを表示させたいアカウントを選んでください。", view=view, ephemeral=True)

# register modal menu
class Modal(discord.ui.Modal, title="アカウント登録"):
	name = discord.ui.TextInput(label="アカウント名", placeholder="例 name#tag")
	memo = discord.ui.TextInput(label="メモ", placeholder="どんなアカウントかわかるようにメモしましょう")
	async def on_submit(self, interaction: discord.Interaction) -> None:
		riotid = self.name.value
		if not re.fullmatch(r'[^\W_]{3,16}(?: [^\W_]{1,15})*#[^\W_]{3,5}', riotid):
			await interaction.response.send_message(f'不明なidです。({riotid})', ephemeral=True)
			return
		await interaction.response.send_message(f'読込中です。しばしお待ちを...  (id:{riotid})', ephemeral=True)
		sp_riotid = riotid.split("#")
		url = f'https://api.henrikdev.xyz/valorant/v2/account/{sp_riotid[0]}/{sp_riotid[1]}?api_key={api_key}'
		async with aiohttp.ClientSession() as session:
			response = await fetch(session, url)
			if response is None:
				await interaction.followup.send(f'不明なidです。({riotid})', ephemeral=True)
				return
		db = Database()
		db.add_id(interaction.user.id)
		db.add_data(interaction.user.id, riotid, response['data']['puuid'], self.memo.value)
		db.close_connection()
		await interaction.followup.send(f'IDの登録が完了しました!! /statusコマンドを試してみてください! ({riotid})', ephemeral=True)

# register command
@tree.command(name='register')
async def register(interaction: discord.Integration):
	await interaction.response.send_modal(Modal())

# rm select menu
class DeleteView(View):
	@discord.ui.select(
		cls=Select,
		placeholder="アカウント選択"
	)
	async def selectMenu(self, interaction: Interaction, select: Select):
		await interaction.response.send_message(f"削除しています", ephemeral=True)
		db = Database()
		data = select.values[0].split(",")
		db.delete_data(interaction.user.id, data[0])
		db.close_connection()
		await interaction.followup.send(f'{data[0]} を削除しました。', ephemeral=True)

# rm command
@tree.command(name='rm')
async def remove_id(interaction: discord.Integration):
	view = DeleteView()
	db = Database()
	data = db.get_data(interaction.user.id)
	if not data:
		await interaction.response.send_message(f"登録されているデータがありません", ephemeral=True)
		return
	for username, puuid, memo in data:
		view.selectMenu.add_option(
			label=username,
			value=f"{username},{puuid},{memo}",
			description=memo,
		)
	db.close_connection()
	await interaction.response.send_message("消すIDを選んでください", view=view, ephemeral=True)

# cc command
@tree.command(name='cc', description='クロスヘアの画像を生成します')
async def crosshair(interaction: discord.Integration, code:str):
	await interaction.response.send_message(f"まて", ephemeral=True)
	enc_code = urllib.parse.quote(code)
	params = {'api_key': f'{api_key}', 'id': f'{enc_code}'}
	url = 'https://api.henrikdev.xyz/valorant/v1/crosshair/generate'
	async with aiohttp.ClientSession() as session:
		response = await fetch(session, url, params)
	if response is None:
		await interaction.followup.send(f"コードが無効です", ephemeral=True)
		return
	xhair_data = response
	xhair_image = os.path.join(os.path.dirname(__file__), 'assets', 'xhair.png')
	with open(xhair_image, "wb") as f:
		f.write(xhair_data)
	basepath = os.path.join(os.path.dirname(__file__), 'assets', 'base.png')
	dst = Image.open(basepath)
	xsrc = Image.open(xhair_image)
	position = (0, 0)
	dst.paste(xsrc, position, xsrc)
	resultpath = os.path.join(os.path.dirname(__file__), 'assets', 'result.png')
	dst.save(resultpath)
	file = discord.File(resultpath, filename='result.png')
	embed = discord.Embed(title=code,description=f"{interaction.user.mention}",colour=0x00b0f4)
	embed.set_image(url=f"attachment://result.png")
	await interaction.followup.send(embed=embed, file=file)

# help command
@tree.command(name='help')
async def help_command(interaction: discord.Integration):
	text = """このBOTは、valorantのアカウント情報を表示させる目的で作られました。アカウントに関連付けられている不変のIDで保存するため、一度保存したアカウントは、riotIDが変えられても現在のIDを取得できます。また、tracker.ggなどのサイトで非公開でも関係なく見ることができます。
※あくまで小規模のサーバーで活用するためのBOTであり、万が一バグが発生した場合でも、軽い気持ちでご理解いただければと思います。

以下はコマンドリストです
	**/register** : IDを登録させることができます。複数登録が可能です。
	**/stats**    : 登録したアカウントの情報を表示させます。アカウント選択メニューがでます。
	**/rm**       : アカウントの登録解除ができます。アカウント選択メニューがでます。
	**/cc {code}  : クロスヘアの画像を生成します。"""
	await interaction.response.send_message(text, ephemeral=True)

client.run(token)