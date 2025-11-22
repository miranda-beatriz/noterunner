import arcade
import random
import json
import os

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "NoteRunner"

PLAYER_SPEED = 6

NOTE_SPEED_START = 2.0
NOTE_SPEED_INCREMENT = 0.4
SPAWN_INTERVAL_START = 0.8
SPAWN_INTERVAL_MIN = 0.25
LEVEL_UP_EVERY = 10

MAX_MISSES = 5

SAVE_FILE = "save_data.json"

ASSETS_DIR = "assets"
BACKGROUND_MUSIC_PATH = os.path.join(ASSETS_DIR, "bg_music.mp3")
CATCH_SOUND_PATH = os.path.join(ASSETS_DIR, "catch.wav")
MISS_SOUND_PATH = os.path.join(ASSETS_DIR, "miss.wav")
NOTE_IMAGE_PATH = os.path.join(ASSETS_DIR, "note.png")
PLAYER_IMAGE_PATH = os.path.join(ASSETS_DIR, "runner.png")

NOTE_SCALE = 0.1
PLAYER_SCALE = 0.2

MUSIC_SPEED_BASE = 1.0
MUSIC_SPEED_INCREMENT = 0.1
MUSIC_SPEED_MAX = 2.0


def load_game_data():
    if not os.path.exists(SAVE_FILE):
        return {"high_score": 0, "last_level": 1}
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("high_score", 0)
        data.setdefault("last_level", 1)
        return data
    except (json.JSONDecodeError, OSError):
        return {"high_score": 0, "last_level": 1}


def save_game_data(high_score: int, last_level: int):
    data = {"high_score": high_score, "last_level": last_level}
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except OSError:
        pass


class Note(arcade.Sprite):
    def __init__(self):
        super().__init__(NOTE_IMAGE_PATH, NOTE_SCALE)
        self.change_y = -NOTE_SPEED_START


class NoteRunnerGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BEIGE)

        self.game_state = "MENU"

        self.player_sprite: arcade.Sprite | None = None
        self.player_list: arcade.SpriteList | None = None
        self.note_list: arcade.SpriteList | None = None

        self.score = 0
        self.level = 1
        self.notes_missed = 0

        self.note_spawn_timer = 0.0
        self.current_spawn_interval = SPAWN_INTERVAL_START
        self.current_note_speed = NOTE_SPEED_START

        data = load_game_data()
        self.high_score = data["high_score"]
        self.last_level = data["last_level"]

        self.music_speed = MUSIC_SPEED_BASE
        self.music_player = None

        self.background_music = None
        self.catch_sound = None
        self.miss_sound = None

        self.load_sounds()

    def load_sounds(self):
        try:
            if os.path.exists(BACKGROUND_MUSIC_PATH):
                self.background_music = arcade.load_sound(BACKGROUND_MUSIC_PATH)
            if os.path.exists(CATCH_SOUND_PATH):
                self.catch_sound = arcade.load_sound(CATCH_SOUND_PATH)
            if os.path.exists(MISS_SOUND_PATH):
                self.miss_sound = arcade.load_sound(MISS_SOUND_PATH)
        except Exception:
            pass

    def play_music(self):
        if self.background_music is None:
            return
        if self.music_player is not None:
            try:
                self.music_player.stop()
            except Exception:
                pass
        try:
            self.music_player = arcade.play_sound(
                self.background_music,
                0.4,
                0.0,
                True,
                self.music_speed,
            )
        except Exception:
            self.music_player = None

    def setup(self):
        self.player_sprite = arcade.Sprite(PLAYER_IMAGE_PATH, PLAYER_SCALE)
        self.player_sprite.center_x = SCREEN_WIDTH / 2
        self.player_sprite.center_y = 125
        self.player_sprite.change_x = 0

        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player_sprite)

        self.note_list = arcade.SpriteList()

        self.score = 0
        self.level = 1
        self.notes_missed = 0

        self.current_note_speed = NOTE_SPEED_START
        self.current_spawn_interval = SPAWN_INTERVAL_START
        self.note_spawn_timer = 0.0

        self.music_speed = MUSIC_SPEED_BASE
        self.play_music()

    def on_draw(self):
        self.clear()

        if self.game_state == "MENU":
            self.draw_menu()
        elif self.game_state == "GAME":
            self.draw_game()
        elif self.game_state == "GAME_OVER":
            self.draw_game_over()

    def draw_menu(self):
        arcade.draw_text(
            "NoteRunner",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT * 0.65,
            arcade.color.BLACK,
            font_size=40,
            anchor_x="center",
        )
        arcade.draw_text(
            "Click to start",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT * 0.52,
            arcade.color.DIM_GRAY,
            font_size=18,
            anchor_x="center",
        )
        arcade.draw_text(
            "Use LEFT/RIGHT arrows or A/D to move",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT * 0.45,
            arcade.color.DIM_GRAY,
            font_size=16,
            anchor_x="center",
        )
        arcade.draw_text(
            "Catch the falling notes and avoid missing too many",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT * 0.38,
            arcade.color.DIM_GRAY,
            font_size=16,
            anchor_x="center",
        )
        arcade.draw_text(
            f"High Score: {self.high_score}",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT * 0.26,
            arcade.color.DARK_GOLDENROD,
            font_size=18,
            anchor_x="center",
        )
        arcade.draw_text(
            f"Last Level Reached: {self.last_level}",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT * 0.2,
            arcade.color.DARK_GOLDENROD,
            font_size=16,
            anchor_x="center",
        )

    def draw_game(self):
        arcade.draw_lbwh_rectangle_filled(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            arcade.color.BEIGE,
        )

        arcade.draw_line(
            0,
            50,
            SCREEN_WIDTH,
            50,
            arcade.color.LIGHT_GRAY,
            2,
        )

        if self.note_list:
            self.note_list.draw()
        if self.player_list:
            self.player_list.draw()

        hud_y = SCREEN_HEIGHT - 20
        arcade.draw_text(
            f"Score: {self.score}",
            10,
            hud_y,
            arcade.color.BLACK,
            font_size=14,
        )
        arcade.draw_text(
            f"Level: {self.level}",
            160,
            hud_y,
            arcade.color.BLACK,
            font_size=14,
        )
        arcade.draw_text(
            f"Missed: {self.notes_missed}/{MAX_MISSES}",
            290,
            hud_y,
            arcade.color.BLACK,
            font_size=14,
        )
        arcade.draw_text(
            f"High Score: {self.high_score}",
            SCREEN_WIDTH - 200,
            hud_y,
            arcade.color.DARK_GOLDENROD,
            font_size=14,
        )

    def draw_game_over(self):
        arcade.draw_lbwh_rectangle_filled(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            arcade.color.BEIGE,
        )
        arcade.draw_text(
            "Game Over",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT * 0.6,
            arcade.color.DARK_RED,
            font_size=40,
            anchor_x="center",
        )
        arcade.draw_text(
            f"Final Score: {self.score}",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT * 0.5,
            arcade.color.BLACK,
            font_size=20,
            anchor_x="center",
        )
        arcade.draw_text(
            f"Level Reached: {self.level}",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT * 0.44,
            arcade.color.BLACK,
            font_size=18,
            anchor_x="center",
        )
        arcade.draw_text(
            "Click to return to menu",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT * 0.34,
            arcade.color.DIM_GRAY,
            font_size=16,
            anchor_x="center",
        )

    def on_update(self, delta_time: float):
        if self.game_state != "GAME":
            return

        self.player_sprite.center_x += self.player_sprite.change_x

        if self.player_sprite.left < 0:
            self.player_sprite.left = 0
        if self.player_sprite.right > SCREEN_WIDTH:
            self.player_sprite.right = SCREEN_WIDTH

        self.note_spawn_timer += delta_time
        if self.note_spawn_timer >= self.current_spawn_interval:
            self.spawn_note()
            self.note_spawn_timer = 0.0

        for note in self.note_list:
            note.center_y += note.change_y

        hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.note_list
        )
        for note in hit_list:
            self.score += 1
            note.remove_from_sprite_lists()
            if self.catch_sound is not None:
                try:
                    arcade.play_sound(self.catch_sound, 0.6)
                except Exception:
                    pass
            if self.score % LEVEL_UP_EVERY == 0:
                self.level_up()

        for note in list(self.note_list):
            if note.top < 0:
                self.notes_missed += 1
                if self.miss_sound is not None:
                    try:
                        arcade.play_sound(self.miss_sound, 0.4)
                    except Exception:
                        pass
                note.remove_from_sprite_lists()

        if self.notes_missed >= MAX_MISSES:
            self.end_game()

    def spawn_note(self):
        note = Note()
        note.center_x = random.randint(20, SCREEN_WIDTH - 20)
        note.center_y = SCREEN_HEIGHT + 20
        note.change_y = -self.current_note_speed
        self.note_list.append(note)

    def level_up(self):
        self.level += 1
        self.current_note_speed += NOTE_SPEED_INCREMENT
        self.current_spawn_interval = max(
            SPAWN_INTERVAL_MIN,
            SPAWN_INTERVAL_START - (self.level - 1) * 0.05,
        )
        self.music_speed = min(
            MUSIC_SPEED_MAX,
            MUSIC_SPEED_BASE + (self.level - 1) * MUSIC_SPEED_INCREMENT,
        )
        if self.music_player is not None:
            try:
                self.music_player.pitch = self.music_speed
            except AttributeError:
                self.play_music()

    def end_game(self):
        if self.score > self.high_score:
            self.high_score = self.score
        self.last_level = max(self.last_level, self.level)
        save_game_data(self.high_score, self.last_level)
        if self.music_player is not None:
            try:
                self.music_player.stop()
            except Exception:
                pass
            self.music_player = None
        self.game_state = "GAME_OVER"

    def on_key_press(self, key, modifiers):
        if self.game_state == "GAME":
            if key in (arcade.key.LEFT, arcade.key.A):
                self.player_sprite.change_x = -PLAYER_SPEED
            elif key in (arcade.key.RIGHT, arcade.key.D):
                self.player_sprite.change_x = PLAYER_SPEED
        if key == arcade.key.ESCAPE:
            self.game_state = "MENU"

    def on_key_release(self, key, modifiers):
        if self.game_state == "GAME":
            if key in (arcade.key.LEFT, arcade.key.A, arcade.key.RIGHT, arcade.key.D):
                self.player_sprite.change_x = 0

    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_state in ("MENU", "GAME_OVER"):
            self.game_state = "GAME"
            self.setup()


def main():
    game = NoteRunnerGame()
    arcade.run()


if __name__ == "__main__":
    main()
