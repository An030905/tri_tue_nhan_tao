import arcade
import arcade.gui
import os
import math
from engine import *

BOARD_WIDTH = 640
TOP_PANEL_HEIGHT = 160
WIDTH = 760
HEIGHT = BOARD_WIDTH + TOP_PANEL_HEIGHT
BOARD_X = (WIDTH - BOARD_WIDTH) // 2
BOARD_Y = 55
TILE = BOARD_WIDTH // 8
PIECE_SIZE = 72

COLOR_LIGHT = (245, 250, 255)
COLOR_DARK = (42, 139, 214)
COLOR_WHITE_PIECE = (238, 224, 196)
COLOR_SELECTED = (246, 246, 105, 200)
COLOR_LAST_MOVE = (186, 202, 68, 150)
COLOR_HINT = (0, 0, 0, 40)
COLOR_CHECK = (235, 97, 80)


class AnimatedPiece(arcade.Sprite):
    """Sprite with smooth move and scale animation."""

    def __init__(self, piece_name, base_path, r, c):
        path = os.path.join(base_path, "assets", f"{piece_name}.png")
        super().__init__(path)

        self.width = PIECE_SIZE
        self.height = PIECE_SIZE
        if piece_name.startswith("w"):
            self.color = COLOR_WHITE_PIECE

        self.grid_r = r
        self.grid_c = c

        self.target_x = BOARD_X + c * TILE + TILE // 2
        self.target_y = BOARD_Y + (7 - r) * TILE + TILE // 2

        self.center_x = self.target_x
        self.center_y = self.target_y

        self.easing_speed = 0.18
        self.current_scale = 1.0
        self.target_scale = 1.0

    def update(self, delta_time: float = 0.0):
        if self.center_x != self.target_x or self.center_y != self.target_y:
            self.center_x += (self.target_x - self.center_x) * self.easing_speed
            self.center_y += (self.target_y - self.center_y) * self.easing_speed

            if abs(self.target_x - self.center_x) < 0.5 and abs(self.target_y - self.center_y) < 0.5:
                self.center_x = self.target_x
                self.center_y = self.target_y

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

        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.v_box = arcade.gui.UIBoxLayout(vertical=False, space_between=15)

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

        self.pause_btn = arcade.gui.UIFlatButton(text="Pause", width=115, style=btn_style)
        self.pause_btn.on_click = self.on_click_pause

        self.rollback_btn = arcade.gui.UIFlatButton(text="Rollback", width=115, style=btn_style)
        self.rollback_btn.on_click = self.on_click_rollback

        self.new_game_btn = arcade.gui.UIFlatButton(text="New Game", width=115, style=btn_style)
        self.new_game_btn.on_click = self.on_click_new_game

        self.v_box.add(self.pause_btn)
        self.v_box.add(self.rollback_btn)
        self.v_box.add(self.new_game_btn)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(child=self.v_box, anchor_x="center", anchor_y="top", align_y=-15)
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
                        sprite.center_x = BOARD_X + animate_move[1] * TILE + TILE // 2
                        sprite.center_y = BOARD_Y + (7 - animate_move[0]) * TILE + TILE // 2
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

        board_left = BOARD_X
        board_right = BOARD_X + BOARD_WIDTH
        board_bottom = BOARD_Y
        board_top = BOARD_Y + BOARD_WIDTH

        arcade.draw_lrbt_rectangle_filled(board_left - 12, board_right + 12, board_bottom - 12, board_top + 12,
                                          (18, 20, 24))
        arcade.draw_lrbt_rectangle_outline(board_left - 12, board_right + 12, board_bottom - 12, board_top + 12,
                                           (72, 75, 84), 2)
        for r in range(8):
            for c in range(8):
                current_color = COLOR_LIGHT if (r + c) % 2 == 0 else COLOR_DARK
                l, b = BOARD_X + c * TILE, BOARD_Y + (7 - r) * TILE
                arcade.draw_lrbt_rectangle_filled(l, l + TILE, b, b + TILE, current_color)

        if self.last_move:
            r1, c1, r2, c2 = self.last_move
            for r, c in [(r1, c1), (r2, c2)]:
                l, b = BOARD_X + c * TILE, BOARD_Y + (7 - r) * TILE
                arcade.draw_lrbt_rectangle_filled(l, l + TILE, b, b + TILE, COLOR_LAST_MOVE)

        if self.selected:
            r, c = self.selected
            l, b = BOARD_X + c * TILE, BOARD_Y + (7 - r) * TILE
            arcade.draw_lrbt_rectangle_filled(l, l + TILE, b, b + TILE, COLOR_SELECTED)

        for _, _, r, c in self.valid_moves:
            cx, cy = BOARD_X + c * TILE + TILE // 2, BOARD_Y + (7 - r) * TILE + TILE // 2
            if self.board[r][c] == "":
                arcade.draw_circle_filled(cx, cy, 14, COLOR_HINT)
            else:
                l, b = BOARD_X + c * TILE, BOARD_Y + (7 - r) * TILE
                arcade.draw_lrbt_rectangle_outline(l, l + TILE, b, b + TILE, COLOR_HINT, 6)

        self.piece_sprite_list.draw()

        for i in range(8):
            color = COLOR_LIGHT if i % 2 != 0 else COLOR_DARK
            arcade.draw_text(
                text=str(8 - i),
                x=BOARD_X + 4,
                y=BOARD_Y + (7 - i) * TILE + TILE - 4,
                color=color,
                font_size=11,
                bold=True,
                anchor_x="left",
                anchor_y="top"
            )

            color = COLOR_LIGHT if i % 2 == 0 else COLOR_DARK
            arcade.draw_text(
                text=chr(97 + i),
                x=BOARD_X + i * TILE + TILE - 4,
                y=BOARD_Y + 4,
                color=color,
                font_size=11,
                bold=True,
                anchor_x="right",
                anchor_y="bottom"
            )

        panel_bottom = BOARD_Y + BOARD_WIDTH + 12
        arcade.draw_lrbt_rectangle_filled(0, WIDTH, panel_bottom, HEIGHT, (33, 35, 41))
        arcade.draw_line(0, panel_bottom, WIDTH, panel_bottom, (20, 22, 26), 4)

        row_bottom = HEIGHT - 65
        row_top = HEIGHT - 15
        arcade.draw_lrbt_rectangle_filled(20, 175, row_bottom, row_top, (45, 48, 56))
        arcade.draw_lrbt_rectangle_outline(20, 175, row_bottom, row_top, (65, 68, 76), 2)
        arcade.draw_text("CHESS AI", 97, HEIGHT - 43,
                         arcade.color.GOLD, 24, font_name="calibri", anchor_x="center", bold=True)

        arcade.draw_lrbt_rectangle_filled(WIDTH - 175, WIDTH - 20, row_bottom + 5, row_top - 5, (25, 27, 32))

        if self.is_ai_thinking:
            alpha = int(175 + 80 * math.sin(self.time_elapsed * 5))
            arcade.draw_text("AI is thinking...", WIDTH - 97, row_bottom + 17,
                             (235, 151, 78, alpha), 14, font_name="calibri", anchor_x="center", italic=True, bold=True)
        else:
            arcade.draw_text("Your Turn", WIDTH - 97, row_bottom + 17,
                             (118, 150, 86), 14, font_name="calibri", anchor_x="center", bold=True)

        self.manager.draw()

        if is_in_check(self.board, "w", self.move_log) and not self.game_over:
            arcade.draw_text("CHECK!", BOARD_X + BOARD_WIDTH // 2 + 2, BOARD_Y + BOARD_WIDTH // 2 - 2, (0, 0, 0, 150), 50,
                             anchor_x="center", anchor_y="center", bold=True)
            arcade.draw_text("CHECK!", BOARD_X + BOARD_WIDTH // 2, BOARD_Y + BOARD_WIDTH // 2, COLOR_CHECK, 50, anchor_x="center",
                             anchor_y="center", bold=True)

        if self.game_over:
            arcade.draw_lrbt_rectangle_filled(board_left, board_right, board_bottom, board_top, (0, 0, 0, 190))
            msg = "YOU WIN" if self.winner == "w" else "YOU LOST" if self.winner == "b" else "DRAW"
            msg_color = (118, 150, 86) if self.winner == "w" else (235, 97, 80) if self.winner == "b" else (200, 200,
                                                                                                            200)
            arcade.draw_text(msg, BOARD_X + BOARD_WIDTH // 2, BOARD_Y + BOARD_WIDTH // 2 + 20, msg_color, 55, font_name="calibri",
                             anchor_x="center", anchor_y="center", bold=True)
            arcade.draw_text("Press 'New Game' to restart", BOARD_X + BOARD_WIDTH // 2, BOARD_Y + BOARD_WIDTH // 2 - 30, (200, 200, 200),
                             16, anchor_x="center", anchor_y="center")

        elif self.is_paused:
            arcade.draw_lrbt_rectangle_filled(board_left, board_right, board_bottom, board_top, (0, 0, 0, 180))
            arcade.draw_text("PAUSED", BOARD_X + BOARD_WIDTH // 2, BOARD_Y + BOARD_WIDTH // 2, arcade.color.WHITE, 60, anchor_x="center",
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
        if self.game_over or self.is_paused or self.is_ai_thinking:
            return

        if not (BOARD_X <= x < BOARD_X + BOARD_WIDTH and BOARD_Y <= y < BOARD_Y + BOARD_WIDTH):
            return

        board_x = x - BOARD_X
        board_y = y - BOARD_Y
        c, r = int(board_x // TILE), int(7 - (board_y // TILE))
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
