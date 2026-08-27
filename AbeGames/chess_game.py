import chess
import chess.engine

class Chess:
    def __init__(self, color="white"):
        self.stockfish_engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish") 
        self.peice_translator = {
            "p" : "pawn",
            "k" : "king",
            "n" : "knight",
            "q" : "queen",
            "r" : "rook",
            "b" : "bishop"
            }
        if color == "black":
            self.color = chess.BLACK
        else:
            self.color = chess.WHITE

    def main_loop(self):
        while True:
            if self.board.turn == self.color:
                self.result = self.stockfish_engine.play(self.board, limit=chess.engine.Limit(time=1, depth=25))
                self.result_text = str(self.result.move)
                self.peice_to_move = self.board.piece_at(self.result.move.from_square)
                self.clean_result = f"I will move my {self.peice_translator[str(self.peice_to_move)]} from {self.result_text[:2]} to {self.result_text[2:4]}"
                print(self.clean_result)


            while True:
                try:
                    my_move = input("Your move: ")
                    my_move = chess.Move.from_uci(my_move)
                    if not my_move in self.board.legal_moves:
                        print("No cheating!")
                        continue

                    self.board.push(my_move)
                    break

                except ValueError:
                    print("Invalid input!")

    def start_game(self, color="white"):
        self.return_board = chess.Board()

        if color == "black":
            color = chess.BLACK
        else:
            color = chess.WHITE

        return self.return_board, color

    def move(self, board, move, color):
        if board.turn != color:
            try:
                my_move = chess.Move.from_uci(move)
                if not my_move in board.legal_moves:
                    return False
                
                board.push(my_move)
                return True

            except ValueError:
                return False

    def generate_move(self, board, color):
        if board.turn == color:
            result = self.stockfish_engine.play(board, limit=chess.engine.Limit(depth=20))
            result_text = str(result.move)
            peice_to_move = board.piece_at(result.move.from_square)
            if len(result_text) == 4:
                clean_result = f"I will move my {self.peice_translator[str(peice_to_move)]} from {result_text[:2]} to {result_text[2:4]}"
                prompt_result = f"[code] It is your turn on chess, Abe. Tell the user your move, in a very casual and natraul-sounding form, but be extremely competitive. Do not ask any follow up questions. You have decided to move your {self.peice_translator[str(peice_to_move)]} from {result_text[:2]} to {result_text[2:4]}."
            elif len(result_text) == 5:
                clean_result = f"I will move my {self.peice_translator[str(peice_to_move)]} from {result_text[:2]} to {result_text[2:4]}, and change it to a {result_text[:2]} to {result_text[4]}."
                prompt_result = f"[code] It is your turn on chess, Abe. Tell the user your move, in a very casual and natraul-sounding form, but be extremely competitive. You have decided to move your {self.peice_translator[str(peice_to_move)]} from {result_text[:2]} to {result_text[2:4]}, and change it to a {result_text[4]}."

            in_check = board.is_check()
            board.push(result.move)
            return clean_result, prompt_result, in_check 
        else:
            return None, None, None

    def get_is_finished(self, board):
        return board.is_game_over()

    
if __name__ == '__main__':
    game = Chess(color="black")
    game.main_loop()
