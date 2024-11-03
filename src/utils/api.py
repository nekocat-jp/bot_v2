async def fetch(session, url, params=None):
	try:
		async with session.get(url, params=params) as response:
			if response.status == 200:
				type = response.headers.get('Content-Type', '')
				if 'application/json' in type:
					return await response.json()
				else:
					return await response.read()
			else:
				return None
	except Exception as e:
		print(f"Unexpected error: {e}")
	return None