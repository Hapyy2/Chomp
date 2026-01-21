import socket
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog

HOST = '127.0.0.1'
PORT = 5050
BUF_SIZE = 1024

class ChompApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chomp - Klient")
        self.root.geometry("500x550")
        
        self.sock = None
        self.connected = False
        
        self.my_id = -1
        self.rows = 0
        self.cols = 0
        self.buttons = []
        self.is_my_turn = False
        
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)
        
        self.current_frame = None
        
        if self.connect_to_server():
            self.show_menu()
            self.recv_thread = threading.Thread(target=self.receive_loop, daemon=True)
            self.recv_thread.start()
        else:
            messagebox.showerror("Błąd", "Nie można połączyć z serwerem!")
            self.root.destroy()

    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            self.connected = True
            return True
        except:
            return False

    def send_cmd(self, cmd):
        if self.connected:
            try:
                self.sock.send(f"{cmd}\n".encode())
            except:
                pass

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()

    def show_menu(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.container)
        self.current_frame.pack(fill="both", expand=True)
        
        tk.Label(self.current_frame, text="CHOMP - Menu Główne", font=("Arial", 20, "bold")).pack(pady=40)
        
        tk.Button(self.current_frame, text="GRAJ (Lista Lobby)", font=("Arial", 14), width=20, 
                  command=self.show_lobby_list).pack(pady=10)
        
        tk.Button(self.current_frame, text="WYJDŹ", font=("Arial", 14), width=20, 
                  command=self.on_close).pack(pady=10)

    def show_lobby_list(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.container)
        self.current_frame.pack(fill="both", expand=True)
        
        tk.Label(self.current_frame, text="Dostępne Gry", font=("Arial", 16)).pack(pady=10)
        
        self.listbox = tk.Listbox(self.current_frame, width=50, height=10)
        self.listbox.pack(pady=10)
        
        btn_frame = tk.Frame(self.current_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Odśwież", command=self.refresh_lobbies).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Dołącz", command=self.join_selected_lobby).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Stwórz Nową", command=self.create_lobby_dialog).grid(row=0, column=2, padx=5)
        
        tk.Button(self.current_frame, text="Powrót", command=self.show_menu).pack(pady=20)
        
        self.refresh_lobbies()

    def show_game_interface(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.container)
        self.current_frame.pack(fill="both", expand=True)
        
        info_text = f"Jesteś Graczem {self.my_id + 1}"
        self.lbl_info = tk.Label(self.current_frame, text=info_text, font=("Arial", 12, "bold"))
        self.lbl_info.pack(pady=5)
        
        self.lbl_status = tk.Label(self.current_frame, text="Oczekiwanie...", fg="blue")
        self.lbl_status.pack(pady=5)
        
        self.board_frame = tk.Frame(self.current_frame)
        self.board_frame.pack(pady=10)
        
        self.buttons = []
        for r in range(self.rows):
            row_btns = []
            for c in range(self.cols):
                btn = tk.Button(self.board_frame, width=4, height=2, bg="#5C4033",
                                command=lambda x=r, y=c: self.send_move(x, y))
                btn.grid(row=r, column=c, padx=2, pady=2)
                row_btns.append(btn)
            self.buttons.append(row_btns)
            
        self.buttons[0][0].config(text="☠", fg="red")
        
        bottom_frame = tk.Frame(self.current_frame)
        bottom_frame.pack(pady=10, fill="x")
        
        self.btn_restart = tk.Button(bottom_frame, text="Zagraj Ponownie", state="disabled", 
                                     command=self.vote_restart)
        self.btn_restart.pack(side="left", padx=20)
        
        tk.Button(bottom_frame, text="Wyjdź do Menu", 
                  command=self.leave_game).pack(side="right", padx=20)

    # --- LOGIKA ---

    def refresh_lobbies(self):
        self.send_cmd("LIST")

    def create_lobby_dialog(self):
        name = simpledialog.askstring("Nowa Gra", "Nazwa pokoju:")
        if not name: return
        try:
            r_str = simpledialog.askstring("Wymiary", "Liczba wierszy (2-10):", initialvalue="5")
            c_str = simpledialog.askstring("Wymiary", "Liczba kolumn (2-10):", initialvalue="4")
            rows, cols = int(r_str), int(c_str)
            if rows < 2 or cols < 2 or rows > 10 or cols > 10: raise ValueError
        except:
            messagebox.showerror("Błąd", "Złe wymiary.")
            return
        self.send_cmd(f"CREATE {name} {rows} {cols}")

    def join_selected_lobby(self):
        selection = self.listbox.curselection()
        if not selection: return
        item = self.listbox.get(selection[0])
        lobby_id = item.split(" | ")[0]
        self.send_cmd(f"JOIN {lobby_id}")

    def send_move(self, r, c):
        if self.is_my_turn:
            self.send_cmd(f"MOVE {r} {c}")

    def vote_restart(self):
        self.send_cmd("RESTART")
        self.btn_restart.config(text="Czekam na 2. gracza...", state="disabled")

    def leave_game(self):
        self.send_cmd("LEAVE")
        self.show_menu()

    def on_close(self):
        self.connected = False
        try:
            self.sock.close()
        except:
            pass
        self.root.destroy()

    # --- ODBIÓR DANYCH ---

    def receive_loop(self):
        buffer = ""
        while self.connected:
            try:
                data = self.sock.recv(BUF_SIZE).decode()
                if not data: break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.process_server_message(line)
            except:
                break

    def process_server_message(self, msg):
        parts = msg.split()
        if not parts: return
        cmd = parts[0]
        
        if cmd == "LOBBY_LIST":
            if self.listbox:
                self.listbox.delete(0, tk.END)
                for item in parts[1:]:
                    lid, name, count = item.split(":")
                    self.listbox.insert(tk.END, f"{lid} | {name} ({count}/2)")
        
        elif cmd == "JOINED":
            self.my_id = int(parts[2])
            self.rows = int(parts[3])
            self.cols = int(parts[4])
            self.root.after(0, self.show_game_interface)
            
        elif cmd == "UPDATE":
            turn = int(parts[1])
            board_str = parts[2]
            self.root.after(0, lambda: self.update_board_gui(turn, board_str))

        elif cmd == "RESET":
             turn = int(parts[1])
             board_str = parts[2]
             self.root.after(0, lambda: self.reset_gui_state(turn, board_str))
        
        elif cmd == "VOTE_ACCEPTED":
            pass 

        elif cmd == "GAMEOVER":
            winner = int(parts[1])
            self.root.after(0, lambda: self.handle_gameover(winner))
            
        elif cmd == "OPPONENT_LEFT":
            self.send_cmd("LEAVE")
            
            self.root.after(0, lambda: messagebox.showinfo("Info", "Przeciwnik wyszedł z gry."))
            self.root.after(0, self.show_lobby_list)

        elif cmd == "ERROR":
            self.root.after(0, lambda: messagebox.showerror("Błąd", "Nie można wykonać akcji."))

    def update_board_gui(self, turn, board_str):
        self.is_my_turn = (turn == self.my_id)
        if self.is_my_turn:
            self.lbl_status.config(text="TWOJA TURA", fg="green")
            self.board_frame.config(bg="#e6ffe6")
        else:
            self.lbl_status.config(text="Ruch przeciwnika...", fg="red")
            self.board_frame.config(bg="#ffe6e6")

        idx = 0
        for r in range(self.rows):
            for c in range(self.cols):
                if board_str[idx] == '0':
                    self.buttons[r][c].config(bg="#D3D3D3", state="disabled", relief="flat")
                else:
                    self.buttons[r][c].config(bg="#5C4033", state="normal", relief="raised")
                idx += 1

    def reset_gui_state(self, turn, board_str):
        self.btn_restart.config(text="Zagraj Ponownie", state="disabled")
        self.update_board_gui(turn, board_str)

    def handle_gameover(self, winner):
        if winner == self.my_id:
            self.lbl_status.config(text="WYGRANA!", fg="gold")
        else:
            self.lbl_status.config(text="PORAŻKA...", fg="black")
        
        for r in range(self.rows):
            for c in range(self.cols):
                self.buttons[r][c].config(state="disabled")
        
        self.btn_restart.config(state="normal")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

if __name__ == "__main__":
    app = ChompApp()
    app.run()