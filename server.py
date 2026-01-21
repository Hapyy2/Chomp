import socket
import threading
import uuid

HOST = '127.0.0.1'
PORT = 5050
BUF_SIZE = 1024

lobbies = {}
lobbies_lock = threading.Lock()

class Lobby:
    def __init__(self, lobby_id, name, rows, cols):
        self.id = lobby_id
        self.name = name
        self.rows = int(rows)
        self.cols = int(cols)
        self.players = [] 
        self.board = []
        self.turn_idx = 0 
        self.game_over = False
        self.restart_votes = set()
        self.init_board()

    def init_board(self):
        self.board = [[1 for _ in range(self.cols)] for _ in range(self.rows)]
        self.game_over = False
        self.turn_idx = 0
        self.restart_votes.clear()

    def broadcast(self, message):
        to_remove = []
        for p in self.players:
            try:
                p.send(f"{message}\n".encode())
            except:
                to_remove.append(p)
        for p in to_remove:
            if p in self.players:
                self.players.remove(p)

    def get_state_str(self):
        return "".join(["".join(map(str, row)) for row in self.board])

    def reset_game(self):
        self.init_board()
        self.broadcast(f"RESET {self.turn_idx} {self.get_state_str()}")

def handle_client(conn, addr):
    print(f"[NOWY KLIENT] {addr} połączony.")
    current_lobby_id = None
    player_id = -1 

    try:
        while True:
            data = conn.recv(BUF_SIZE).decode().strip()
            if not data: break
            
            commands = data.split('\n')
            
            for cmd_line in commands:
                parts = cmd_line.split()
                if not parts: continue
                cmd = parts[0]

                if cmd == "LIST":
                    response = "LOBBY_LIST"
                    with lobbies_lock:
                        for l_id, l in lobbies.items():
                            response += f" {l_id}:{l.name}:{len(l.players)}"
                    conn.send(f"{response}\n".encode())

                elif cmd == "CREATE":
                    name, r, c = parts[1], parts[2], parts[3]
                    new_id = str(uuid.uuid4())[:8]
                    with lobbies_lock:
                        new_lobby = Lobby(new_id, name, r, c)
                        new_lobby.players.append(conn)
                        lobbies[new_id] = new_lobby
                    
                    current_lobby_id = new_id
                    player_id = 0
                    conn.send(f"JOINED {new_id} {player_id} {r} {c}\n".encode())
                    conn.send(f"UPDATE {new_lobby.turn_idx} {new_lobby.get_state_str()}\n".encode())

                elif cmd == "JOIN":
                    l_id = parts[1]
                    with lobbies_lock:
                        if l_id in lobbies:
                            lobby = lobbies[l_id]
                            if len(lobby.players) < 2:
                                lobby.players.append(conn)
                                current_lobby_id = l_id
                                player_id = 1
                                conn.send(f"JOINED {l_id} {player_id} {lobby.rows} {lobby.cols}\n".encode())
                                lobby.broadcast(f"UPDATE {lobby.turn_idx} {lobby.get_state_str()}")
                            else:
                                conn.send("ERROR Lobby_pełne\n".encode())
                        else:
                            conn.send("ERROR Lobby_nie_istnieje\n".encode())

                elif cmd == "LEAVE":
                    if current_lobby_id:
                        with lobbies_lock:
                            if current_lobby_id in lobbies:
                                lobby = lobbies[current_lobby_id]
                                if conn in lobby.players:
                                    lobby.players.remove(conn)
                                    if len(lobby.players) > 0:
                                        lobby.broadcast("OPPONENT_LEFT")
                                    
                                    if len(lobby.players) == 0:
                                        del lobbies[current_lobby_id]
                                        print(f"Lobby {current_lobby_id} usunięte (puste).")
                        current_lobby_id = None
                        player_id = -1

                elif cmd == "MOVE" and current_lobby_id:
                    r, c = int(parts[1]), int(parts[2])
                    lobby = lobbies[current_lobby_id]

                    if len(lobby.players) < 2:
                        continue 

                    if player_id == lobby.turn_idx and not lobby.game_over:
                        if r == 0 and c == 0:
                            lobby.game_over = True
                            winner = 1 - player_id 
                            lobby.broadcast(f"GAMEOVER {winner}")
                        else:
                            changed = False
                            for i in range(r, lobby.rows):
                                for j in range(c, lobby.cols):
                                    if lobby.board[i][j] == 1:
                                        lobby.board[i][j] = 0
                                        changed = True
                            
                            if changed:
                                lobby.turn_idx = 1 - lobby.turn_idx
                                lobby.broadcast(f"UPDATE {lobby.turn_idx} {lobby.get_state_str()}")

                elif cmd == "RESTART" and current_lobby_id:
                    with lobbies_lock:
                        lobby = lobbies[current_lobby_id]
                        lobby.restart_votes.add(conn)
                        
                        conn.send("VOTE_ACCEPTED\n".encode())

                        if len(lobby.restart_votes) == 2:
                            lobby.reset_game()

    except Exception as e:
        print(f"Błąd gracza: {e}")
    finally:
        if current_lobby_id:
            with lobbies_lock:
                if current_lobby_id in lobbies:
                    lobby = lobbies[current_lobby_id]
                    if conn in lobby.players:
                        lobby.players.remove(conn)
                        if len(lobby.players) > 0:
                            lobby.broadcast("OPPONENT_LEFT")
                        if len(lobby.players) == 0:
                            del lobbies[current_lobby_id]
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"--- SERWER CHOMP ---")
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()