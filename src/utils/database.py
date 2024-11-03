import sqlite3
import os

class Database:
	def __init__(self, db_name='../resources/userdata.db'):
		base_dir = os.path.dirname(os.path.abspath(__file__))
		db_path = os.path.join(base_dir, db_name)
		os.makedirs(os.path.dirname(db_path), exist_ok=True)

		self.conn = sqlite3.connect(db_path)
		self.cursor = self.conn.cursor()
		self.create_tables()

	def create_tables(self):
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS IDs (
				id INTEGER PRIMARY KEY
			)
		''')

		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS UsernamesPUUIDs (
				id INTEGER,
				username TEXT,
				puuid TEXT,
				memo TEXT,
				FOREIGN KEY(id) REFERENCES IDs(id),
				UNIQUE(id, username)
			)
		''')
		self.conn.commit()

	def add_id(self, id):
		self.cursor.execute('INSERT OR IGNORE INTO IDs (id) VALUES (?)', (id,))
		self.conn.commit()

	def add_data(self, id, username, puuid, memo):
		try:
			self.cursor.execute('INSERT INTO UsernamesPUUIDs (id, username, puuid, memo) VALUES (?, ?, ?, ?)', (id, username, puuid, memo))
			self.conn.commit()
		except sqlite3.IntegrityError:
			print(f"ID {id} に対して username '{username}' は既に存在します。")

	def delete_data(self, id, username):
		self.cursor.execute('DELETE FROM UsernamesPUUIDs WHERE id = ? AND username = ?', (id, username))
		self.conn.commit()
		print(f"ID {id} から username '{username}' のデータを削除しました。")

	def get_data(self, id):
		self.cursor.execute('SELECT username, puuid, memo FROM UsernamesPUUIDs WHERE id = ?', (id,))
		return self.cursor.fetchall()

	def get_detail(self, id, username):
		self.cursor.execute('SELECT puuid, memo FROM UsernamesPUUIDs WHERE id = ? AND username = ?', (id, username))
		result = self.cursor.fetchone()
		if result:
			return result
		else:
			return None

	def close_connection(self):
		self.conn.close()
