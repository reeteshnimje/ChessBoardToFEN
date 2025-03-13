import sys
import chess
import chess.svg
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QLabel, QFileDialog, QVBoxLayout, \
    QWidget, QGridLayout
from PyQt6.QtGui import QClipboard, QPixmap
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import pyqtSignal


class ChessSvgWidget(QSvgWidget):
    square_clicked = pyqtSignal(chess.Square)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.board_size = 400  # Fixed board size
        self.square_size = self.board_size / 8
        self.flipped = False
        self.setFixedSize(self.board_size, self.board_size)
        self.setAcceptDrops(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            square = self.get_square_at_position(event.position().x(), event.position().y())
            if square is not None:
                self.square_clicked.emit(square)

    def get_square_at_position(self, x, y):
        # Ensure x and y are within bounds
        if not (0 <= x < self.board_size and 0 <= y < self.board_size):
            return None

        # Calculate file and rank (0-7)
        file = int(x // self.square_size)
        rank = 7 - int(y // self.square_size)  # Invert because chess ranks start from bottom

        # Adjust for flipped board if needed
        if self.flipped:
            file = 7 - file
            rank = 7 - rank

        # Convert to chess.Square (0-63)
        return chess.square(file, rank)


class ChessboardEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fuss-Free Chessboard Editor")
        self.setGeometry(100, 100, 800, 700)

        self.board = chess.Board()
        self.is_flipped = False
        self.selected_piece = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # FEN Output Box
        self.fen_output = QTextEdit()
        self.fen_output.setReadOnly(True)
        self.fen_output.setMaximumHeight(80)
        layout.addWidget(self.fen_output)

        # SVG Widget to display the board
        self.svg_widget = ChessSvgWidget()
        self.svg_widget.square_clicked.connect(self.handle_square_click)
        layout.addWidget(self.svg_widget, 1, Qt.AlignmentFlag.AlignCenter)


        # Pieces selection layout
        pieces_layout = QGridLayout()
        pieces = ['K', 'Q', 'R', 'B', 'N', 'P', 'k', 'q', 'r', 'b', 'n', 'p']
        piece_buttons = []

        for i, piece in enumerate(pieces):
            row = i // 6
            col = i % 6
            button = QPushButton(piece)
            button.setFixedSize(60, 60)
            button.clicked.connect(lambda checked, p=piece: self.select_piece(p))
            pieces_layout.addWidget(button, row, col)
            piece_buttons.append(button)

        # Add delete button
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda: self.select_piece("DELETE"))
        pieces_layout.addWidget(delete_button, 2, 0, 1, 6)

        layout.addLayout(pieces_layout)

        # Buttons layout
        button_layout = QGridLayout()

        # Copy FEN Button
        copy_button = QPushButton("Copy FEN to Clipboard")
        copy_button.clicked.connect(self.copy_fen)
        button_layout.addWidget(copy_button, 0, 0)

        # Save FEN Button
        save_button = QPushButton("Save FEN to File")
        save_button.clicked.connect(self.save_fen)
        button_layout.addWidget(save_button, 0, 1)

        # Reset Board Button
        reset_button = QPushButton("Reset Board")
        reset_button.clicked.connect(self.reset_board)
        button_layout.addWidget(reset_button, 1, 0)

        # Empty Board Button
        empty_button = QPushButton("Empty Board")
        empty_button.clicked.connect(self.empty_board)
        button_layout.addWidget(empty_button, 1, 1)

        # Flip Board Button
        flip_button = QPushButton("Flip Board")
        flip_button.clicked.connect(self.flip_board)
        button_layout.addWidget(flip_button, 2, 0)

        # Clear Square Button
        clear_button = QPushButton("Clear Square")
        clear_button.clicked.connect(lambda: self.select_piece("CLEAR"))
        button_layout.addWidget(clear_button, 2, 1)

        # Toggle Turn Button
        toggle_turn_button = QPushButton("Toggle Turn (Current: White)")
        toggle_turn_button.clicked.connect(self.toggle_turn)
        button_layout.addWidget(toggle_turn_button, 3, 0, 1, 2)  # Spans both columns
        self.toggle_turn_button = toggle_turn_button  # Store reference for updating text

        layout.addLayout(button_layout)

        # Main widget setup
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Update board display
        self.update_board()

    def update_board(self):
        svg_data = chess.svg.board(
            self.board,
            size=self.svg_widget.board_size,
            flipped=self.is_flipped,
            coordinates=True
        ).encode("utf-8")
        self.svg_widget.load(svg_data)
        self.fen_output.setText(self.board.fen())

    def copy_fen(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.board.fen(), QClipboard.Mode.Clipboard)
        QMessageBox.information(self, "Copied", "FEN copied to clipboard!")

    def save_fen(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save FEN", "fen_log.txt", "Text Files (*.txt)")
        if file_path:
            with open(file_path, "a") as file:
                file.write(self.board.fen() + "\n")
            QMessageBox.information(self, "Saved", "FEN successfully saved!")

    def reset_board(self):
        self.board = chess.Board()
        self.update_board()
        turn_text = "White" if self.board.turn else "Black"
        self.toggle_turn_button.setText(f"Toggle Turn (Current: {turn_text})")
    def empty_board(self):
        self.board.clear()
        self.update_board()
        turn_text = "White" if self.board.turn else "Black"
        self.toggle_turn_button.setText(f"Toggle Turn (Current: {turn_text})")
    def flip_board(self):
        self.is_flipped = not self.is_flipped
        self.svg_widget.flipped = self.is_flipped
        self.update_board()

    def select_piece(self, piece):
        self.selected_piece = piece
        print(f"Selected piece: {piece}")

    def toggle_turn(self):
        # Toggle the turn in the board
        self.board.turn = not self.board.turn

        # Update the button text to reflect current turn
        turn_text = "White" if self.board.turn else "Black"
        self.toggle_turn_button.setText(f"Toggle Turn (Current: {turn_text})")

        # Update the board display and FEN
        self.update_board()

    def handle_square_click(self, square):
        if self.selected_piece:
            if self.selected_piece == "DELETE" or self.selected_piece == "CLEAR":
                self.board.remove_piece_at(square)
            else:
                piece_map = {
                    'K': chess.Piece(chess.KING, chess.WHITE),
                    'Q': chess.Piece(chess.QUEEN, chess.WHITE),
                    'R': chess.Piece(chess.ROOK, chess.WHITE),
                    'B': chess.Piece(chess.BISHOP, chess.WHITE),
                    'N': chess.Piece(chess.KNIGHT, chess.WHITE),
                    'P': chess.Piece(chess.PAWN, chess.WHITE),
                    'k': chess.Piece(chess.KING, chess.BLACK),
                    'q': chess.Piece(chess.QUEEN, chess.BLACK),
                    'r': chess.Piece(chess.ROOK, chess.BLACK),
                    'b': chess.Piece(chess.BISHOP, chess.BLACK),
                    'n': chess.Piece(chess.KNIGHT, chess.BLACK),
                    'p': chess.Piece(chess.PAWN, chess.BLACK)
                }
                self.board.set_piece_at(square, piece_map[self.selected_piece])

            self.update_board()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChessboardEditor()
    window.show()
    sys.exit(app.exec())