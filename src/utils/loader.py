import requests
import os
from utils.error import error_exit

def load_config():
	filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings', 'config.txt')
	config = {}
	try:
		with open(filename, 'r') as file:
			for line in file:
				line = line.strip()
				if line:
					try:
						key, value = line.split('=')
						config[key] = value
					except ValueError:
						print(f"Warning: '{line}'は正しいフォーマット(key=value)ではありません")
	except FileNotFoundError:
		error_exit(f"config.txtが見つかりません")
	except IOError as e:
		error_exit(f"{e}")
	return config

def check_key(api_key):
	r = requests.get(f"https://api.henrikdev.xyz/valorant/v1/version/ap?api_key={api_key}")
	if (r.status_code != 200):
		error_exit("正しくないAPI_KEYです")
	return 0