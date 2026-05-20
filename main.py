import arcade
import arcade.gui
import os
import math
from engine import *

# --- Cấu hình Kích thước & Màu sắc ---
BOARD_WIDTH = 720  # Tăng độ rộng bàn cờ để ô vuông to ra
UI_WIDTH = 220
WIDTH = BOARD_WIDTH + UI_WIDTH
HEIGHT = BOARD_WIDTH
TILE = BOARD_WIDTH // 8  # TILE lúc này sẽ là 90x90
PIECE_SIZE = 80  # Ép cứng kích thước quân cờ giữ nguyên ở 80x80

# Bảng màu cao cấp (Phong cách Modern Wood)
COLOR_LIGHT = (245, 250, 255)
COLOR_DARK = (42, 139, 214)
COLOR_WHITE_PIECE = (238, 224, 196)
COLOR_SELECTED = (246, 246, 105, 200)  # Vàng neon sáng khi chọn
COLOR_LAST_MOVE = (186, 202, 68, 150)  # Vàng xanh cho ô vừa đi
COLOR_HINT = (0, 0, 0, 40)  # Dấu chấm gợi ý
COLOR_CHECK = (235, 97, 80)  # Đỏ pastel cảnh báo chiếu


class AnimatedPiece(arcade.Sprite):
    """Lớp Sprite hỗ trợ hiệu ứng trượt gia tốc và phóng to"""

    def __init__(self, piece_name, base_path, r, c):
        path = os.path.join(base_path, "assets", f"{piece_name}.png")
        super().__init__(path)

        # Cố định kích thước quân cờ (không dùng TILE nữa để tránh quân cờ bị to theo ô)
        self.width = PIECE_SIZE
        self.height = PIECE_SIZE
        if piece_name.startswith("w"):
            self.color = COLOR_WHITE_PIECE

        # Lưu vị trí tọa độ lưới
        self.grid_r = r
        self.grid_c = c

        # Lưu vị trí đích đến của quân cờ (Vẫn căn giữa theo kích thước TILE mới)
        self.target_x = c * TILE + TILE // 2
        self.target_y = (7 - r) * TILE + TILE // 2

        self.center_x = self.target_x
        self.center_y = self.target_y

        self.easing_speed = 0.18
        self.current_scale = 1.0
        self.target_scale = 1.0

    def update(self, delta_time: float = 0.0):
        # 1. Hiệu ứng trượt (Lerp)
        if self.center_x != self.target_x or self.center_y != self.target_y:
            self.center_x += (self.target_x - self.center_x) * self.easing_speed
            self.center_y += (self.target_y - self.center_y) * self.easing_speed

            if abs(self.target_x - self.center_x) < 0.5 and abs(self.target_y - self.center_y) < 0.5:
                self.center_x = self.target_x
                self.center_y = self.target_y

        # 2. Hiệu ứng phóng to/thu nhỏ (Scale Lerp)
        if self.current_scale != self.target_scale:
            self.current_scale += (self.target_scale - self.current_scale) * 0.2
            if abs(self.target_scale - self.current_scale) < 0.01:
                self.current_scale = self.target_scale

            self.scale = (self.current_scale, self.current_scale)


class ChessGame(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "Chess AI - Premium Edition")
        self.base_path = os.path.dirname(__file__)
        arcade.set_background_color((33, 35, 41))

        # --- UI Manager ---
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.v_box = arcade.gui.UIBoxLayout(space_between=15)

        btn_style = {
            "normal": {
                "font_name": ("calibri", "arial"),
                "font_size": 15,
                "font_color": (220, 220, 220),
                "border_width": 2,
                "border_color": (65, 68, 76),
                "bg_color": (45, 48, 56),
            },
            "hover": {
                "font_name": ("calibri", "arial"),
                "font_size": 15,
                "font_color": arcade.color.WHITE,
                "border_width": 2,
                "border_color": (118, 150, 86),
                "bg_color": (60, 64, 73),
            },
            "press": {
                "font_name": ("calibri", "arial"),
                "font_size": 15,
                "font_color": arcade.color.WHITE,
                "border_width": 2,
                "border_color": (246, 246, 105),
                "bg_color": (118, 150, 86),
            }
        }

        self.pause_btn = arcade.gui.UIFlatButton(text="Pause", width=170, style=btn_style)
        self.pause_btn.on_click = self.on_click_pause

        self.rollback_btn = arcade.gui.UIFlatButton(text="Rollback", width=170, style=btn_style)
        self.rollback_btn.on_click = self.on_click_rollback

        self.new_game_btn = arcade.gui.UIFlatButton(text="New Game", width=170, style=btn_style)
        self.new_game_btn.on_click = self.on_click_new_game

        self.v_box.add(self.pause_btn)
        self.v_box.add(self.rollback_btn)
        self.v_box.add(self.new_game_btn)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(child=self.v_box, anchor_x="right", anchor_y="bottom", align_x=-25, align_y=40)
        self.manager.add(anchor)

        self.piece_sprite_list = arcade.SpriteList()
        self.time_elapsed = 0.0
        self.reset_game()

    def reset_game(self):
        self.board = [
            ["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["", "", "", "", "", "", "", ""], ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""], ["", "", "", "", "", "", "", ""],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"]
        ]
        self.move_log, self.selected, self.valid_moves = [], None, []
        self.game_over, self.winner = False, None
        self.is_paused = False
        self.last_move = None
        self.is_ai_thinking = False
        self.pause_btn.text = "Pause"
        self.sync_sprites()

    def rebuild_board_from_log(self):
        self.board = [
            ["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["", "", "", "", "", "", "", ""], ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""], ["", "", "", "", "", "", "", ""],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"]
        ]
        for move, _ in self.move_log:
            self.board = make_move(self.board, move)
        self.last_move = self.move_log[-1][0] if self.move_log else None
        self.sync_sprites()

    def on_click_pause(self, event):
        if self.game_over: return
        self.is_paused = not self.is_paused
        self.pause_btn.text = "Continue" if self.is_paused else "Pause"

    def on_click_rollback(self, event):
        if len(self.move_log) > 0 and not self.is_ai_thinking:
            self.game_over = False
            self.winner = None
            self.move_log.pop()
            if len(self.move_log) > 0:
                self.move_log.pop()
            self.selected, self.valid_moves = None, []
            self.rebuild_board_from_log()

    def on_click_new_game(self, event):
        self.reset_game()

    def sync_sprites(self, animate_move=None):
        self.piece_sprite_list.clear()
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece:
                    sprite = AnimatedPiece(piece, self.base_path, r, c)
                    if animate_move and r == animate_move[2] and c == animate_move[3]:
                        sprite.center_x = animate_move[1] * TILE + TILE // 2
                        sprite.center_y = (7 - animate_move[0]) * TILE + TILE // 2
                    self.piece_sprite_list.append(sprite)

    def on_update(self, delta_time):
        self.time_elapsed += delta_time
        self.piece_sprite_list.update()

        for sprite in self.piece_sprite_list:
            if self.selected and sprite.grid_r == self.selected[0] and sprite.grid_c == self.selected[1]:
                sprite.target_scale = 1.15
            else:
                sprite.target_scale = 1.0

    def on_draw(self):
        self.clear()

        # 1. Vẽ bàn cờ
        for r in range(8):
            for c in range(8):
                current_color = COLOR_LIGHT if (r + c) % 2 == 0 else COLOR_DARK
                l, b = c * TILE, (7 - r) * TILE
                arcade.draw_lrbt_rectangle_filled(l, l + TILE, b, b + TILE, current_color)

        # 1.5 Highlight nước đi trước đó
        if self.last_move:
            r1, c1, r2, c2 = self.last_move
            for r, c in [(r1, c1), (r2, c2)]:
                l, b = c * TILE, (7 - r) * TILE
                arcade.draw_lrbt_rectangle_filled(l, l + TILE, b, b + TILE, COLOR_LAST_MOVE)

        # 2. Highlight ô đang chọn và gợi ý
        if self.selected:
            r, c = self.selected
            l, b = c * TILE, (7 - r) * TILE
            arcade.draw_lrbt_rectangle_filled(l, l + TILE, b, b + TILE, COLOR_SELECTED)

        for _, _, r, c in self.valid_moves:
            cx, cy = c * TILE + TILE // 2, (7 - r) * TILE + TILE // 2
            if self.board[r][c] == "":
                arcade.draw_circle_filled(cx, cy, 14, COLOR_HINT)
            else:
                l, b = c * TILE, (7 - r) * TILE
                arcade.draw_lrbt_rectangle_outline(l, l + TILE, b, b + TILE, COLOR_HINT, 6)

        # 3. Vẽ tất cả quân cờ
        self.piece_sprite_list.draw()

        # 3.5 VẼ TỌA ĐỘ A-H VÀ 1-8 (Căn lề tuyệt đối vào sát góc ô)
        for i in range(8):
            # Số 1-8
            color = COLOR_LIGHT if i % 2 != 0 else COLOR_DARK
            arcade.draw_text(
                text=str(8 - i),
                x=4,
                y=(7 - i) * TILE + TILE - 4,
                color=color,
                font_size=11,
                bold=True,
                anchor_x="left",
                anchor_y="top"
            )

            # Chữ a-h
            color = COLOR_LIGHT if i % 2 == 0 else COLOR_DARK
            arcade.draw_text(
                text=chr(97 + i),
                x=i * TILE + TILE - 4,
                y=4,
                color=color,
                font_size=11,
                bold=True,
                anchor_x="right",
                anchor_y="bottom"
            )

        # 4. Vẽ Giao diện Panel bên phải (UI)
        arcade.draw_lrbt_rectangle_filled(BOARD_WIDTH, WIDTH, 0, HEIGHT, (33, 35, 41))
        arcade.draw_line(BOARD_WIDTH, 0, BOARD_WIDTH, HEIGHT, (20, 22, 26), 4)

        header_y = HEIGHT - 80
        arcade.draw_lrbt_rectangle_filled(BOARD_WIDTH + 15, WIDTH - 15, header_y, HEIGHT - 15, (45, 48, 56))
        arcade.draw_lrbt_rectangle_outline(BOARD_WIDTH + 15, WIDTH - 15, header_y, HEIGHT - 15, (65, 68, 76), 2)
        arcade.draw_text("CHESS AI", BOARD_WIDTH + UI_WIDTH // 2, HEIGHT - 55,
                         arcade.color.GOLD, 24, font_name="calibri", anchor_x="center", bold=True)

        status_y = HEIGHT - 140
        arcade.draw_lrbt_rectangle_filled(BOARD_WIDTH + 15, WIDTH - 15, status_y, status_y + 40, (25, 27, 32))

        if self.is_ai_thinking:
            alpha = int(175 + 80 * math.sin(self.time_elapsed * 5))
            arcade.draw_text("AI is thinking...", BOARD_WIDTH + UI_WIDTH // 2, status_y + 12,
                             (235, 151, 78, alpha), 14, font_name="calibri", anchor_x="center", italic=True, bold=True)
        else:
            arcade.draw_text("Your Turn", BOARD_WIDTH + UI_WIDTH // 2, status_y + 12,
                             (118, 150, 86), 14, font_name="calibri", anchor_x="center", bold=True)

        self.manager.draw()

        # 5. Thông báo Overlay
        if is_in_check(self.board, "w", self.move_log) and not self.game_over:
            arcade.draw_text("CHECK!", BOARD_WIDTH // 2 + 2, BOARD_WIDTH // 2 - 2, (0, 0, 0, 150), 50,
                             anchor_x="center", anchor_y="center", bold=True)
            arcade.draw_text("CHECK!", BOARD_WIDTH // 2, BOARD_WIDTH // 2, COLOR_CHECK, 50, anchor_x="center",
                             anchor_y="center", bold=True)

        if self.game_over:
            arcade.draw_lrbt_rectangle_filled(0, BOARD_WIDTH, 0, BOARD_WIDTH, (0, 0, 0, 190))
            msg = "YOU WIN" if self.winner == "w" else "YOU LOST" if self.winner == "b" else "DRAW"
            msg_color = (118, 150, 86) if self.winner == "w" else (235, 97, 80) if self.winner == "b" else (200, 200,
                                                                                                            200)
            arcade.draw_text(msg, BOARD_WIDTH // 2, BOARD_WIDTH // 2 + 20, msg_color, 55, font_name="calibri",
                             anchor_x="center", anchor_y="center", bold=True)
            arcade.draw_text("Press 'New Game' to restart", BOARD_WIDTH // 2, BOARD_WIDTH // 2 - 30, (200, 200, 200),
                             16, anchor_x="center", anchor_y="center")

        elif self.is_paused:
            arcade.draw_lrbt_rectangle_filled(0, BOARD_WIDTH, 0, BOARD_WIDTH, (0, 0, 0, 180))
            arcade.draw_text("PAUSED", BOARD_WIDTH // 2, BOARD_WIDTH // 2, arcade.color.WHITE, 60, anchor_x="center",
                             anchor_y="center", bold=True)

    def make_ai_move(self, delta_time):
        arcade.unschedule(self.make_ai_move)

        if self.game_over or self.is_paused:
            self.is_ai_thinking = False
            return

        AI_TYPE = "hybrid"
        ai_move = None
        if not is_checkmate(self.board, "b", self.move_log) and not is_stalemate(self.board, "b", self.move_log):
            if AI_TYPE == "random":
                ai_move = random_ai(self.board, "b", self.move_log)
            elif AI_TYPE == "minimax":
                ai_move = minimax_ai(self.board, "b", self.move_log, depth=2)
            elif AI_TYPE == "hybrid":
                ai_move = ai_hybrid(self.board, "b", self.move_log, depth=2, top_n=3)

            if ai_move:
                self.move_log.append((ai_move, self.board[ai_move[0]][ai_move[1]]))
                self.board = make_move(self.board, ai_move)
                self.last_move = ai_move
                self.sync_sprites(animate_move=ai_move)

        if is_checkmate(self.board, "w", self.move_log):
            self.game_over, self.winner = True, "b"
        elif is_checkmate(self.board, "b", self.move_log):
            self.game_over, self.winner = True, "w"
        elif is_stalemate(self.board, "w", self.move_log) or is_stalemate(self.board, "b", self.move_log):
            self.game_over, self.winner = True, "draw"

        self.is_ai_thinking = False

    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_over or self.is_paused or x > BOARD_WIDTH or self.is_ai_thinking:
            return

        c, r = int(x // TILE), int(7 - (y // TILE))
        if not (0 <= r < 8 and 0 <= c < 8): return

        if self.selected is None:
            if self.board[r][c] and self.board[r][c][0] == "w":
                self.selected = (r, c)
                self.valid_moves = [m for m in get_valid_moves(self.board, "w", self.move_log) if
                                    m[0] == r and m[1] == c]
        else:
            move = (self.selected[0], self.selected[1], r, c)
            if move in self.valid_moves:
                self.move_log.append((move, self.board[move[0]][move[1]]))
                self.board = make_move(self.board, move)
                self.last_move = move
                self.sync_sprites(animate_move=move)

                self.selected, self.valid_moves = None, []

                self.is_ai_thinking = True
                arcade.schedule(self.make_ai_move, 0.4)
            else:
                self.selected, self.valid_moves = None, []


if __name__ == "__main__":
    ChessGame()
    arcade.run()
