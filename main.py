# -*- coding: utf-8 -*-
import pygame
import sys
import os
import math
import random
import sqlite3
import hashlib
import socket
import json
import threading
import time

WIDTH, HEIGHT = 1000, 700
FPS = 60
BG, PANEL, PANEL2, PANEL_HOVER = (16, 18, 30), (28, 32, 50), (40, 46, 70), (56, 64, 96)
ACCENT, ACCENT2, TEXT, TEXT_DIM = (90, 200, 255), (255, 190, 80), (230, 236, 248), (135, 145, 172)
GREEN, RED, PURPLE, YELLOW, GOLD, DARK_RED, ORANGE, CYAN = (95, 225, 135), (240, 90, 105), (175, 125, 245), (250, 220,
                                                                                                             90), (255,
                                                                                                                   210,
                                                                                                                   70), (
    200, 60, 80), (255, 170, 90), (0, 255, 255)

TIERS, DIVS = ["青铜", "白银", "黄金", "铂金", "星钻", "皇冠"], ["V", "IV", "III", "II", "I"]
STARS_PER_DIV, STARS_PER_TIER, ACE_START, ACE_MAX = 2, 10, 60, 109
RANK_QUALIFY = ACE_MAX

CHAR_FART, CHAR_COMPILE, CHAR_SPARK, CHAR_WALL, CHAR_TERMINATE = "fart", "compile", "spark", "wall", "terminate"
CHAR_HEAL, CHAR_WATER, CHAR_IFDER, CHAR_TAOZHI, CHAR_HOWEI, CHAR_BOSS = "heal", "water", "ifder", "taozhi", "haowei", "boss"
ALL_CHARS = [CHAR_FART, CHAR_COMPILE, CHAR_SPARK, CHAR_WALL, CHAR_TERMINATE, CHAR_HEAL, CHAR_WATER, CHAR_IFDER,
             CHAR_TAOZHI, CHAR_HOWEI, CHAR_BOSS]

CHAR_INFO = {
    CHAR_FART: {"name": "放屁大王", "color": GREEN},
    CHAR_COMPILE: {"name": "编译永远是神", "color": CYAN},
    CHAR_SPARK: {"name": "电刺刺客", "color": PURPLE},
    CHAR_WALL: {"name": "墙皮大师", "color": (185, 175, 150)},
    CHAR_TERMINATE: {"name": "终止进程", "color": DARK_RED},
    CHAR_HEAL: {"name": "嘴嘴香", "color": ORANGE},
    CHAR_WATER: {"name": "矿泉水", "color": (120, 220, 255)},
    CHAR_IFDER: {"name": "if der", "color": (255, 100, 200)},
    CHAR_TAOZHI: {"name": "桃枝气树", "color": (255, 105, 180)},
    CHAR_HOWEI: {"name": "豪之艺术", "color": (255, 215, 0)},
    CHAR_BOSS: {"name": "老板", "color": (139, 69, 19)},
}
SKILL_INTERVALS = {CHAR_FART: 3.0, CHAR_COMPILE: 8.0, CHAR_SPARK: 3.0, CHAR_WALL: 10.0, CHAR_TERMINATE: 22.0,
                   CHAR_HEAL: 10.0, CHAR_WATER: 30.0, CHAR_IFDER: 6.0, CHAR_TAOZHI: 10.0, CHAR_HOWEI: 30.0,
                   CHAR_BOSS: 40.0}
MAPS = {"map1": {"name": "训练营", "cols": 24, "rows": 18}, "map2": {"name": "大乱斗场", "cols": 42, "rows": 35},
        "map3": {"name": "巨人遗迹", "cols": 20, "rows": 22}, "map4": {"name": "无限训练场", "cols": 100, "rows": 100}}
MODES = {1: {"name": "1v1 单挑", "per_team": 1}, 2: {"name": "2v2 双排", "per_team": 2},
         3: {"name": "3v3 团战", "per_team": 3}}
AI_NAMES = ["闪电侠", "暗夜猎手", "狂暴之刃", "钢铁之心", "冰雪女神", "火焰法师", "影之舞", "雷霆战神", "星辰之子",
            "幽冥刺客", "龙魂战士", "风云剑客"]

_font_cache = {}


def get_font(size, bold=False):
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    candidates = ["microsoftyahei", "msyh", "simhei", "simsun", "dengxian", "notosanscjksc", "notosansmonocjksc",
                  "wenquanyimicrohei", "pingfangsc", "heiti", "stheiti", "arialunicodems"]
    font = None
    for name in candidates:
        try:
            path = pygame.font.match_font(name, bold=bold)
        except Exception:
            path = None
        if path:
            try:
                font = pygame.font.Font(path, size)
                break
            except Exception:
                pass
    if font is None:
        font = pygame.font.SysFont(None, size, bold=bold)
    _font_cache[key] = font
    return font


def draw_text(surf, text, font, color, pos, center=False, right=False, midleft=False):
    img = font.render(str(text), True, color)
    rect = img.get_rect()
    if center:
        rect.center = pos
    elif right:
        rect.topright = pos
    elif midleft:
        rect.midleft = pos
    else:
        rect.topleft = pos
    surf.blit(img, rect)


def draw_panel(surf, rect, color=PANEL, radius=12, border=None, width=2):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surf, border, rect, width=width, border_radius=radius)


def draw_button(surf, rect, text, font, mouse_pos, color=ACCENT, enabled=True):
    hover = enabled and rect.collidepoint(mouse_pos)
    bg = PANEL_HOVER if hover else PANEL2
    if not enabled:
        bg = (36, 38, 50)
    draw_panel(surf, rect, bg, radius=10, border=color if enabled else (70, 74, 90))
    draw_text(surf, text, font, TEXT if enabled else (110, 115, 130), rect.center, center=True)


def rank_name(stars, is_god):
    if is_god:
        return "无敌战神"
    if stars >= ACE_START:
        return "超级王牌%d星" % min(50, stars - ACE_START + 1)
    tier = stars // STARS_PER_TIER
    div = (stars % STARS_PER_TIER) // STARS_PER_DIV
    if tier >= len(TIERS):
        tier = len(TIERS) - 1
        div = 4
    return TIERS[tier] + DIVS[div]


def rank_color(stars, is_god):
    if is_god:
        return GOLD
    if stars >= ACE_START:
        return (255, 120, 90)
    colors = [(170, 120, 80), (200, 200, 210), (240, 200, 80), (120, 230, 200), (150, 170, 255), (230, 130, 240)]
    return colors[min(stars // STARS_PER_TIER, len(colors) - 1)]


def display_name(username):
    return username[3:] if username.startswith("AI_") else username


class NetworkClient:
    def __init__(self):
        self.sock = None
        self.is_online = False
        self.room_id = None
        self.server_ip = "192.168.2.30"  # 写死局域网IP
        self.connect_attempts = 0
        self.is_connecting = False

    def start_auto_connect(self):
        if self.is_connecting: return
        self.is_connecting = True
        self.connect_attempts = 0

        def connect_task():
            while self.connect_attempts < 5:
                try:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.settimeout(2)
                    self.sock.connect((self.server_ip, 8888))
                    self.is_online = True
                    break
                except Exception:
                    self.connect_attempts += 1
                    time.sleep(0.5)
            self.is_connecting = False

        threading.Thread(target=connect_task, daemon=True).start()

    def req(self, action, data):
        if not self.is_online or not self.sock:
            return {"success": False, "msg": "离线模式"}
        try:
            self.sock.sendall((json.dumps({"action": action, "data": data}) + "\n").encode('utf-8'))
            buffer = ""
            while "\n" not in buffer:
                d = self.sock.recv(4096)
                if not d:
                    break
                buffer += d.decode('utf-8')
            return json.loads(buffer.strip())
        except:
            self.is_online = False
            return {"success": False, "msg": "网络断开"}


net = NetworkClient()
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "duanwei_local.db")


def db_connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def hash_pw(pw):
    return hashlib.sha256(("duanwei_liehuo_" + pw).encode("utf-8")).hexdigest()


def init_local_db():
    conn = db_connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT UNIQUE NOT NULL, 
            password TEXT NOT NULL,
            stars INTEGER DEFAULT 0, 
            wins INTEGER DEFAULT 0, 
            losses INTEGER DEFAULT 0, 
            is_god INTEGER DEFAULT 0, 
            is_ai INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    if conn.execute("SELECT COUNT(*) FROM players WHERE is_ai=1").fetchone()[0] < 10:
        for name in AI_NAMES[:10]:
            conn.execute(
                "INSERT INTO players (username, password, stars, wins, losses, is_god, is_ai) VALUES (?,?,?,?,?,?,1)",
                ("AI_" + name, "ai", random.randint(5, 108), random.randint(20, 90), random.randint(15, 70),
                 random.randint(0, 1)))
        conn.commit()
    conn.close()


class Trap:
    def __init__(self, x, y, kind, team):
        self.x, self.y = float(x), float(y)
        self.kind, self.team = kind, team
        self.hit = set()
        self.life = 10.0 if kind == "wall" else 3.0
        self.r = 34.0 if kind == "wall" else 30.0
        self.max_life = self.life


class CooldownBall:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.r, self.collected = 15.0, False
        self.phase = random.random() * math.pi * 2


class Fighter:
    def __init__(self, x, y, char_type, name, rank_text, is_player, team):
        self.x, self.y, self.vx, self.vy = float(x), float(y), 0.0, 0.0
        self.r, self.hp, self.max_hp = 20.0, 100.0, 100.0
        self.char_type, self.name, self.rank_text = char_type, name, rank_text
        self.is_player, self.team, self.original_team = is_player, team, team
        self.skill_interval = SKILL_INTERVALS.get(char_type, 3.0)
        self.skill_timer = self.skill_interval
        self.silence, self.flash, self.heal_flash, self.wobble = 0.0, 0.0, 0.0, 0.0
        self.ai_level, self.rooted, self.idx = 0, False, 0
        self.doom_timer, self.doom_owner = 0.0, None
        self.charm_timer, self.skill_locked = 0.0, False
        self.water_timer, self.water_angle, self.water_hit_cd = 0.0, 0.0, {}
        self.immune_timer, self.lifetime = 0.0, -1.0


class Battle:
    def __init__(self, game, map_key, mode, player_team, enemy_team, difficulty):
        self.game, self.map_key, self.mode, self.difficulty = game, map_key, mode, difficulty
        self.is_training = (map_key == "map4")
        if self.is_training:
            self.arena, self.cols, self.rows = pygame.Rect(50, 100, WIDTH - 100, HEIGHT - 200), 100, 100
        else:
            m = MAPS[map_key]
            self.cols, self.rows = m["cols"], m["rows"]
            scale = min((WIDTH - 100) / self.cols, 460 / self.rows)
            w, h = int(self.cols * scale), int(self.rows * scale)
            self.arena = pygame.Rect((WIDTH - w) // 2, 140 + (460 - h) // 2, w, h)
        self.traps, self.floaters, self.cooldown_balls, self.obstacles = [], [], [], []
        self.giant_timer = 60.0
        if map_key == "map3":
            self.obstacles = [
                pygame.Rect(self.arena.left + self.arena.width // 4, self.arena.top + 40, 60, 120),
                pygame.Rect(self.arena.left + self.arena.width * 3 // 4 - 60, self.arena.bottom - 160, 60, 120),
                pygame.Rect(self.arena.centerx - 40, self.arena.centery - 20, 80, 40),
                pygame.Rect(self.arena.left + 40, self.arena.centery - 50, 50, 100),
                pygame.Rect(self.arena.right - 90, self.arena.centery - 50, 50, 100)
            ]
        self.finished, self.winner, self.end_timer = False, -1, 0.0
        self.fighters = []
        self.inf_cd, self.god_mode, self.no_dmg = False, False, False
        self.pending_spawn = None

        n = len(player_team)
        spacing = min(90.0, self.arena.height / (n + 0.5))
        for i, (ct, nm, rk, ip) in enumerate(player_team):
            y = self.arena.centery + (i - (n - 1) / 2.0) * spacing
            f = Fighter(self.arena.left + 100, y, ct, nm, rk, ip, 0)
            f.ai_level, f.idx = 1, len(self.fighters)
            self.fighters.append(f)
        for i, (ct, nm, rk, ip) in enumerate(enemy_team):
            y = self.arena.centery + (i - (n - 1) / 2.0) * spacing
            f = Fighter(self.arena.right - 100, y, ct, nm, rk, ip, 1)
            f.ai_level = min(2, difficulty + 1)
            f.idx = len(self.fighters)
            self.fighters.append(f)
        self.player_fighter = self.fighters[0]

    def spawn_fighter(self, char_type, team, x, y):
        f = Fighter(x, y, char_type, "测试员", "无", False, team)
        f.idx = len(self.fighters)
        f.ai_level = 1 if team == 0 else 2
        self.fighters.append(f)

    def get_eff_team(self, f):
        return 1 - f.original_team if f.charm_timer > 0 else f.team

    def update(self, dt):
        if self.finished and not self.is_training:
            self.end_timer += dt
            return
        if self.map_key == "map3" and self.giant_timer > 0:
            self.giant_timer -= dt
            if self.giant_timer <= 0:
                for _ in range(random.randint(3, 5)):
                    self.cooldown_balls.append(CooldownBall(random.randint(self.arena.left + 30, self.arena.right - 30),
                                                            random.randint(self.arena.top + 30,
                                                                           self.arena.bottom - 30)))
                self._add_float(self.arena.centerx, self.arena.top + 20, "巨人降临！", GOLD)
        for b in self.cooldown_balls:
            if b.collected:
                continue
            b.phase += dt * 3
            for f in self.fighters:
                if f.hp <= 0:
                    continue
                if math.hypot(f.x - b.x, f.y - b.y) < f.r + b.r:
                    b.collected = True
                    if random.random() < 0.3:
                        f.skill_timer = 0
                        self._add_float(f.x, f.y - 30, "技能重置!", GREEN)
                    else:
                        f.skill_locked = True
                        self._add_float(f.x, f.y - 30, "技能封锁!", DARK_RED)
        for f in self.fighters:
            if f.charm_timer > 0:
                f.charm_timer -= dt
                if f.charm_timer <= 0:
                    f.charm_timer = 0
                    self._add_float(f.x, f.y - 30, "阵营恢复", ACCENT)
            if f.immune_timer > 0:
                f.immune_timer -= dt
            if f.lifetime > 0:
                f.lifetime -= dt
                if f.lifetime <= 0:
                    f.hp = 0
            f.rooted = (f.doom_timer > 0)
            if f.water_timer > 0:
                f.water_timer -= dt
                f.water_angle += 3.5 * dt
                for other in self.fighters:
                    if other.hp <= 0 or other.idx == f.idx:
                        continue
                    if other.idx in f.water_hit_cd and f.water_hit_cd[other.idx] > 0:
                        f.water_hit_cd[other.idx] -= dt
                    for ang in (f.water_angle, f.water_angle + math.pi):
                        px, py = f.x + math.cos(ang) * 60, f.y + math.sin(ang) * 60
                        if math.hypot(other.x - px, other.y - py) < 22 + other.r:
                            if other.idx not in f.water_hit_cd or f.water_hit_cd[other.idx] <= 0:
                                f.water_hit_cd[other.idx] = 0.5
                                if self.get_eff_team(other) == self.get_eff_team(f):
                                    other.hp = min(other.max_hp, other.hp + 10)
                                    other.heal_flash = 0.3
                                else:
                                    self._damage(other, 10, "water")
        for t in self.traps:
            if t.kind != "wall":
                continue
            for f in self.fighters:
                if f.hp <= 0 or self.get_eff_team(f) == t.team:
                    continue
                if math.hypot(f.x - t.x, f.y - t.y) < t.r + f.r * 0.7:
                    f.rooted = True
        for f in self.fighters:
            if f.hp <= 0:
                continue
            if f.doom_timer > 0:
                if f.doom_owner and f.doom_owner.hp <= 0:
                    f.doom_timer, f.doom_owner = 0, None
                else:
                    f.doom_timer -= dt
                    if f.doom_timer <= 0:
                        f.doom_timer, f.hp = 0, 0
            if self.is_training and self.inf_cd:
                f.skill_timer = 0.0
                if f.char_type == CHAR_HOWEI:
                    f.immune_timer = 10.0
        for f in self.fighters:
            self._update_fighter(f, dt)
        self._separate()
        for t in self.traps[:]:
            t.life -= dt
            if t.life <= 0:
                self.traps.remove(t)
                continue
            for f in self.fighters:
                if f.hp <= 0 or self.get_eff_team(f) == t.team:
                    continue
                dist = math.hypot(f.x - t.x, f.y - t.y)
                if t.kind == "wall":
                    if dist < t.r + f.r * 0.7 and f.idx not in t.hit:
                        t.hit.add(f.idx)
                        self._damage(f, 5, "wall")
                else:
                    if f.idx in t.hit:
                        continue
                    if dist < t.r + f.r * 0.85:
                        t.hit.add(f.idx)
                        self._damage(f, 10, t.kind)
                        if t.kind == "spark":
                            f.silence = max(f.silence, 2.0)
        for fl in self.floaters[:]:
            fl[4] -= dt
            fl[1] -= 45 * dt
            if fl[4] <= 0:
                self.floaters.remove(fl)
        if not self.is_training:
            if not any(self.get_eff_team(f) == 0 and f.hp > 0 for f in self.fighters) and not any(
                    self.get_eff_team(f) == 1 and f.hp > 0 for f in self.fighters):
                self._finish(-1)
            elif not any(self.get_eff_team(f) == 0 and f.hp > 0 for f in self.fighters):
                self._finish(1)
            elif not any(self.get_eff_team(f) == 1 and f.hp > 0 for f in self.fighters):
                self._finish(0)

    def _pick_target(self, f):
        my_team = self.get_eff_team(f)
        enemies = [o for o in self.fighters if self.get_eff_team(o) != my_team and o.hp > 0]
        if not enemies:
            return None
        if f.char_type == CHAR_HEAL and f.ai_level > 0:
            allies = [o for o in self.fighters if self.get_eff_team(o) == my_team and o is not f and o.hp > 0]
            if allies:
                return min(allies, key=lambda o: o.hp / o.max_hp)
        if f.ai_level >= 2:
            return min(enemies, key=lambda o: o.hp)
        return min(enemies, key=lambda o: math.hypot(o.x - f.x, o.y - f.y))

    def _update_fighter(self, f, dt):
        if f.hp <= 0:
            return
        my_team = self.get_eff_team(f)
        enemies = [o for o in self.fighters if self.get_eff_team(o) != my_team and o.hp > 0]
        if not enemies:
            return
        target = self._pick_target(f)
        if not target:
            return
        dx, dy = target.x - f.x, target.y - f.y
        d = math.hypot(dx, dy) or 0.001
        if not f.rooted:
            acc = 640.0
            ax, ay = dx / d * acc, dy / d * acc
            if d < 60:
                ax -= dx / d * acc * 0.9
                ay -= dy / d * acc * 0.9
            if f.ai_level >= 1:
                dodge = 1.0 if f.ai_level == 1 else 1.8
                for t in self.traps:
                    if t.team == my_team:
                        continue
                    tx, ty = f.x - t.x, f.y - t.y
                    td = math.hypot(tx, ty)
                    safe = t.r + f.r + 80
                    if 0.1 < td < safe:
                        wgt = (safe - td) / 80.0
                        ax += tx / td * acc * dodge * wgt
                        ay += ty / td * acc * dodge * wgt
            f.wobble += dt
            seed = 1.7 + f.idx * 1.3
            ax += math.cos(f.wobble * 2.1 + seed) * acc * 0.38
            ay += math.sin(f.wobble * 1.7 + seed) * acc * 0.38
            f.vx += ax * dt
            f.vy += ay * dt
            max_speed = 300.0 + f.ai_level * 45.0
            if f.ai_level >= 2 and my_team == 1:
                max_speed *= 1.15
            sp = math.hypot(f.vx, f.vy)
            if sp > max_speed:
                f.vx, f.vy = f.vx / sp * max_speed, f.vy / sp * max_speed
            damp = max(0.0, 1.0 - 3.2 * dt)
            f.vx *= damp
            f.vy *= damp
            f.x += f.vx * dt
            f.y += f.vy * dt
        else:
            f.vx, f.vy = 0, 0
        a = self.arena
        if f.x - f.r < a.left:
            f.x = a.left + f.r
            f.vx = abs(f.vx) * 0.65 + 45
        elif f.x + f.r > a.right:
            f.x = a.right - f.r
            f.vx = -abs(f.vx) * 0.65 - 45
        if f.y - f.r < a.top:
            f.y = a.top + f.r
            f.vy = abs(f.vy) * 0.65 + 45
        elif f.y + f.r > a.bottom:
            f.y = a.bottom - f.r
            f.vy = -abs(f.vy) * 0.65 - 45
        for obs in self.obstacles:
            cx = max(obs.left, min(f.x, obs.right))
            cy = max(obs.top, min(f.y, obs.bottom))
            odx, ody = f.x - cx, f.y - cy
            odist = math.hypot(odx, ody)
            if odist < f.r:
                if odist > 0:
                    f.x = cx + odx / odist * f.r
                    f.y = cy + ody / odist * f.r
                else:
                    f.y = obs.top - f.r
        if f.doom_timer > 0 or f.skill_locked:
            pass
        elif f.silence > 0:
            f.silence -= dt
        else:
            f.skill_timer -= dt
            if f.skill_timer <= 0:
                f.skill_timer = f.skill_interval
                self._use_skill(f)
        if f.flash > 0:
            f.flash -= dt
        if f.heal_flash > 0:
            f.heal_flash -= dt

    def _separate(self):
        for i in range(len(self.fighters)):
            for j in range(i + 1, len(self.fighters)):
                a, b = self.fighters[i], self.fighters[j]
                if a.hp <= 0 or b.hp <= 0:
                    continue
                dx, dy = b.x - a.x, b.y - a.y
                d = math.hypot(dx, dy)
                min_d = a.r + b.r
                if 0.001 < d < min_d:
                    nx, ny = dx / d, dy / d
                    push = (min_d - d) * 0.5
                    a.x -= nx * push
                    a.y -= ny * push
                    b.x += nx * push
                    b.y += ny * push

    def _use_skill(self, f):
        if f.char_type in (CHAR_FART, CHAR_SPARK, CHAR_WALL):
            kind = "fart" if f.char_type == CHAR_FART else ("spark" if f.char_type == CHAR_SPARK else "wall")
            self.traps.append(Trap(f.x, f.y, kind, self.get_eff_team(f)))
        elif f.char_type == CHAR_TERMINATE:
            enemies = [o for o in self.fighters if
                       self.get_eff_team(o) != self.get_eff_team(f) and o.hp > 0 and o.doom_timer <= 0]
            if enemies:
                target = random.choice(enemies)
                target.doom_timer, target.doom_owner = 10.0, f
        elif f.char_type == CHAR_HEAL:
            allies = [o for o in self.fighters if self.get_eff_team(o) == self.get_eff_team(f)]
            dead = [o for o in allies if o.hp <= 0]
            if dead:
                target = random.choice(dead)
                target.hp, target.max_hp = target.max_hp * 0.5, target.max_hp + 10
                target.heal_flash = 0.6
            else:
                alive = [o for o in allies if o.hp > 0]
                if alive:
                    target = min(alive, key=lambda o: o.hp / o.max_hp)
                    target.hp = min(target.max_hp, target.hp + 50)
                    target.max_hp += 10
                    target.heal_flash = 0.6
        elif f.char_type == CHAR_COMPILE:
            for t in self.traps:
                if t.team != self.get_eff_team(f):
                    t.team = self.get_eff_team(f)
                    t.hit.clear()
        elif f.char_type == CHAR_WATER:
            f.water_timer, f.water_angle = 8.0, 0.0
            f.water_hit_cd.clear()
        elif f.char_type == CHAR_IFDER:
            targets = [o for o in self.fighters if o.hp > 0]
            if targets:
                target = random.choice(targets)
                state = random.choice(["if", "der"])
                if state == "if":
                    if random.random() < 0.5:
                        self._damage(target, target.hp, "taozhi")
                    else:
                        target.rooted = False
                        target.silence = 0
                        target.doom_timer = 0
                else:
                    target.charm_timer = 10.0
                    target.original_team = self.get_eff_team(target)
        elif f.char_type == CHAR_TAOZHI:
            enemies = [o for o in self.fighters if self.get_eff_team(o) != self.get_eff_team(f) and o.hp > 0]
            if enemies:
                target = min(enemies, key=lambda o: math.hypot(o.x - f.x, o.y - f.y))
                target.rooted = True
                self._damage(target, target.max_hp * 0.9, "taozhi")
                target.silence = max(target.silence, 2.0)
        elif f.char_type == CHAR_HOWEI:
            f.immune_timer = 10.0
        elif f.char_type == CHAR_BOSS:
            for i in range(2):
                new_ct = random.choice(ALL_CHARS)
                sx = max(self.arena.left + 40, min(self.arena.right - 40, f.x + random.randint(-60, 60)))
                sy = max(self.arena.top + 40, min(self.arena.bottom - 40, f.y + random.randint(-60, 60)))
                new_f = Fighter(sx, sy, new_ct, "雇佣兵%d" % (i + 1), "无", False, self.get_eff_team(f))
                new_f.idx = len(self.fighters)
                new_f.lifetime = 90.0
                new_f.ai_level = 1
                self.fighters.append(new_f)

    def _damage(self, f, amount, kind):
        if self.is_training and (self.no_dmg or (self.god_mode and f.team == 0)):
            return
        if f.immune_timer > 0:
            return
        f.hp = max(0.0, f.hp - amount)
        f.flash = 0.25
        color = GREEN if kind == "fart" else (YELLOW if kind == "spark" else (220, 210, 190) if kind == "wall" else RED)
        self._add_float(f.x, f.y - 26, "-%d" % amount, color)

    def _add_float(self, x, y, text, color):
        self.floaters.append([float(x), float(y), str(text), color, 0.9])

    def _finish(self, winner):
        if not self.finished:
            self.finished, self.winner, self.end_timer = True, winner, 0.0

    def draw(self, surf):
        a = self.arena
        pygame.draw.rect(surf, (22, 26, 42), a, border_radius=8)
        pygame.draw.rect(surf, (28, 34, 54), a.inflate(-8, -8), border_radius=6)
        for c in range(1, self.cols):
            pygame.draw.line(surf, (34, 40, 62), (a.left + int(a.width * c / self.cols), a.top + 3),
                             (a.left + int(a.width * c / self.cols), a.bottom - 3), 1)
        for r in range(1, self.rows):
            pygame.draw.line(surf, (34, 40, 62), (a.left + 3, a.top + int(a.height * r / self.rows)),
                             (a.right - 3, a.top + int(a.height * r / self.rows)), 1)
        pygame.draw.rect(surf, ACCENT, a, width=3, border_radius=8)
        for obs in self.obstacles:
            pygame.draw.rect(surf, (60, 64, 80), obs, border_radius=4)
            pygame.draw.rect(surf, (90, 96, 120), obs, 2, border_radius=4)
        for b in self.cooldown_balls:
            if not b.collected:
                r = b.r + math.sin(b.phase) * 3
                pygame.draw.circle(surf, (100, 255, 200), (int(b.x), int(b.y)), int(r))
                pygame.draw.circle(surf, (255, 255, 255), (int(b.x), int(b.y)), int(r), 2)
        for t in self.traps:
            self._draw_trap(surf, t)
        for f in self.fighters:
            self._draw_fighter(surf, f)
        font_f = get_font(20, True)
        for fl in self.floaters:
            alpha = max(0.0, min(1.0, fl[4] / 0.9))
            col = tuple(int(c * (0.4 + 0.6 * alpha)) for c in fl[3])
            draw_text(surf, fl[2], font_f, col, (fl[0], fl[1]), center=True)
        if self.map_key == "map3" and self.giant_timer > 0:
            draw_text(surf, "巨人降临倒计时: %ds" % int(self.giant_timer), get_font(16, True), GOLD,
                      (a.centerx, a.top - 20), center=True)
        if not self.is_training:
            self._draw_team_panels(surf)
        self._draw_hud(surf)
        if self.finished and not self.is_training:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 110))
            surf.blit(overlay, (0, 0))
            txt, col = ("胜  利", GREEN) if self.winner == 0 else (
                ("失  败", RED) if self.winner == 1 else ("平  局", TEXT_DIM))
            draw_text(surf, txt, get_font(56, True), col, (WIDTH // 2, HEIGHT // 2 - 20), center=True)

    def _draw_team_panels(self, surf):
        left_space, right_space = self.arena.left - 20, WIDTH - self.arena.right - 20
        if left_space < 130 or right_space < 130:
            return
        self._draw_one_team_panel(surf, 0, pygame.Rect(10, self.arena.top, left_space, self.arena.height), ACCENT,
                                  "我方队伍")
        self._draw_one_team_panel(surf, 1,
                                  pygame.Rect(self.arena.right + 10, self.arena.top, right_space, self.arena.height),
                                  RED, "敌方队伍")

    def _draw_one_team_panel(self, surf, team, panel, accent, title):
        members = [f for f in self.fighters if self.get_eff_team(f) == team]
        if not members:
            return
        n, alive = len(members), sum(1 for f in members if f.hp > 0)
        tbar = pygame.Rect(panel.x, panel.y, panel.w, 28)
        draw_panel(surf, tbar, PANEL, radius=8, border=accent)
        draw_text(surf, "%s %d/%d" % (title, alive, n), get_font(13, True), accent, (tbar.centerx, tbar.centery),
                  center=True)
        pad, card_h = 6, min(100, (panel.h - 28 - 6 * (n + 1)) // max(1, n))
        if card_h < 60:
            card_h = 60
        for i, f in enumerate(members):
            cy = panel.y + 28 + pad + i * (card_h + pad)
            info, dead = CHAR_INFO[f.char_type], f.hp <= 0
            draw_panel(surf, pygame.Rect(panel.x, cy, panel.w, card_h), PANEL2 if not dead else (32, 34, 48), radius=8,
                       border=info["color"] if not dead else (70, 74, 90), width=2)
            draw_text(surf, info["name"][:5], get_font(13, True), TEXT if not dead else TEXT_DIM,
                      (panel.x + 10, cy + 10))
            draw_text(surf, f.name[:6], get_font(11), TEXT_DIM, (panel.x + 10, cy + 30))
            bw, bh, bx, by = panel.w - 20, 6, panel.x + 10, cy + card_h - 12
            pygame.draw.rect(surf, (40, 44, 62), (bx, by, bw, bh), border_radius=3)
            ww = int(bw * max(0.0, f.hp / f.max_hp))
            if ww > 0:
                pygame.draw.rect(surf, GREEN if f.hp > f.max_hp * 0.5 else RED, (bx, by, ww, bh), border_radius=3)

    def _draw_trap(self, surf, t):
        x, y, ratio = int(t.x), int(t.y), t.life / t.max_life
        if t.kind == "fart":
            pygame.draw.circle(surf, (100, 235, 140, int(90 * ratio + 40)), (x, y),
                               int(t.r * (0.85 + 0.15 * math.sin(t.life * 6))))
        elif t.kind == "spark":
            pygame.draw.polygon(surf, YELLOW, [
                (x + math.cos(math.pi * 2 * i / 16 + t.life * 1.5) * (t.r if i % 2 == 0 else t.r * 0.55),
                 y + math.sin(math.pi * 2 * i / 16 + t.life * 1.5) * (t.r if i % 2 == 0 else t.r * 0.55)) for i in
                range(16)], 2)
        else:
            pygame.draw.rect(surf, (170, 160, 140), (x - t.r, y - t.r, t.r * 2, t.r * 2), border_radius=6)

    def _draw_fighter(self, surf, f):
        x, y = int(f.x), int(f.y)
        if f.hp <= 0:
            pygame.draw.circle(surf, (70, 74, 90), (x, y), int(f.r * 0.7))
            return
        info = CHAR_INFO[f.char_type]
        base = info["color"]
        body = (255, 255, 255) if f.flash > 0 else ((255, 100, 200) if f.charm_timer > 0 else base)
        if f.water_timer > 0:
            for ang in (f.water_angle, f.water_angle + math.pi):
                pygame.draw.circle(surf, (80, 180, 255), (int(f.x + math.cos(ang) * 60), int(f.y + math.sin(ang) * 60)),
                                   18)
        if f.char_type == CHAR_FART:
            pygame.draw.circle(surf, body, (x, y), int(f.r))
        elif f.char_type == CHAR_SPARK:
            pygame.draw.polygon(surf, body, [(x + math.cos(math.pi * 2 * i / 6 + f.wobble * 0.6) * f.r,
                                              y + math.sin(math.pi * 2 * i / 6 + f.wobble * 0.6) * f.r) for i in
                                             range(6)])
        elif f.char_type == CHAR_WALL:
            pygame.draw.rect(surf, body, (x - int(f.r), y - int(f.r), int(f.r) * 2, int(f.r) * 2), border_radius=4)
        elif f.char_type == CHAR_TERMINATE:
            pygame.draw.polygon(surf, body,
                                [(x, y - int(f.r)), (x + int(f.r), y), (x, y + int(f.r)), (x - int(f.r), y)])
        else:
            pygame.draw.circle(surf, body, (x, y), int(f.r))
        draw_text(surf, "你" if f.is_player else ("友" if f.original_team == 0 else "敌"), get_font(12, True),
                  ACCENT if f.is_player else (GREEN if f.original_team == 0 else RED), (x, y - int(f.r) - 16),
                  center=True)
        if f.immune_timer > 0:
            pygame.draw.circle(surf, GOLD, (x, y), int(f.r) + 8, 3)
        if f.doom_timer > 0:
            pygame.draw.circle(surf, DARK_RED, (x, y), int(f.r) + 6, 3)
        bw, bh, bx, by = 44, 5, x - 22, y - int(f.r) - 32
        pygame.draw.rect(surf, (40, 44, 62), (bx, by, bw, bh), border_radius=2)
        w = int(bw * (f.hp / f.max_hp))
        if w > 0:
            pygame.draw.rect(surf, GREEN if f.hp > f.max_hp * 0.5 else RED, (bx, by, w, bh), border_radius=2)

    def _draw_hud(self, surf):
        if self.is_training:
            draw_text(surf, "无限训练场 (F12 呼出控制台)", get_font(20, True), GREEN, (WIDTH // 2, 30), center=True)
            if self.pending_spawn:
                draw_text(surf, "点击场地放置", get_font(16, True), YELLOW, (WIDTH // 2, HEIGHT - 130), center=True)
            return
        team0 = [f for f in self.fighters if self.get_eff_team(f) == 0]
        team1 = [f for f in self.fighters if self.get_eff_team(f) == 1]
        hp0, hp1 = sum(max(0, f.hp) for f in team0), sum(max(0, f.hp) for f in team1)
        max0, max1 = sum(f.max_hp for f in team0) or 1, sum(f.max_hp for f in team1) or 1
        bar0, bar1 = pygame.Rect(30, 34, 380, 20), pygame.Rect(WIDTH - 410, 34, 380, 20)
        pygame.draw.rect(surf, (40, 44, 62), bar0, border_radius=10)
        pygame.draw.rect(surf, GREEN, (bar0.x, bar0.y, int(bar0.w * hp0 / max0), bar0.h), border_radius=10)
        pygame.draw.rect(surf, (40, 44, 62), bar1, border_radius=10)
        pygame.draw.rect(surf, RED,
                         (bar1.x + bar1.w - int(bar1.w * hp1 / max1), bar1.y, int(bar1.w * hp1 / max1), bar1.h),
                         border_radius=10)
        draw_text(surf, "我方 %d/%d" % (hp0, max0), get_font(15), TEXT, (bar0.x + 4, bar0.y - 22))
        draw_text(surf, "敌方 %d/%d" % (hp1, max1), get_font(15), TEXT, (bar1.x + 4, bar1.y - 22))
        draw_text(surf, "%s · %s" % (MAPS[self.map_key]["name"], MODES[self.mode]["name"]), get_font(20, True), ACCENT,
                  (WIDTH // 2, 44), center=True)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("段位大乱斗")
        self.clock = pygame.time.Clock()
        self.conn = db_connect()
        self.running = True
        self.state = "login"

        # 自动开始连接
        net.start_auto_connect()

        self.username = self.password = self.msg = ""
        self.focus = self.msg_timer = 0
        self.msg_color = RED
        self.player = None
        self.lobby_team, self.lobby_mode, self.lobby_map = [], 1, "map1"
        self.selected_char_idx, self.target_member_idx = 0, 0
        self.match_time = self.match_dots = 0.0
        self.opp_info = None
        self.battle = self.result = None
        self.rank_tab = 0
        self.mouse_pos = (0, 0)
        self.sim_timer = 2.0
        self.training_has_enemy = False
        self.show_console = False
        self.console_team = 0
        self.console_char_idx = 0
        self.recruit_list = []
        self.poll_timer = 0.0

    def set_msg(self, text, color=RED):
        self.msg, self.msg_color, self.msg_timer = text, color, 3.0

    def refresh_player(self):
        if net.is_online:
            res = net.req("login",
                          {"username": self.player["username"], "password": self.player.get("password_hash", "dummy")})
            if res.get("success"):
                self.player = res["data"]
        elif self.player:
            self.player = self.conn.execute("SELECT * FROM players WHERE id=?", (self.player["id"],)).fetchone()

    def simulate_ai_battle(self):
        if net.is_online:
            return
        rows = self.conn.execute("SELECT id, stars, wins, losses FROM players WHERE is_ai=1").fetchall()
        if len(rows) >= 2:
            a, b = random.sample(rows, 2)
            self.conn.execute("UPDATE players SET stars=?, wins=? WHERE id=?",
                              (min(109, a["stars"] + 1), a["wins"] + 1, a["id"]))
            self.conn.execute("UPDATE players SET stars=?, losses=? WHERE id=?",
                              (max(0, b["stars"] - 1), b["losses"] + 1, b["id"]))
            self.conn.commit()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.mouse_pos = pygame.mouse.get_pos()
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if self.state == "login":
                self.ev_login(event)
            elif self.state == "menu":
                self.ev_menu(event)
            elif self.state == "lobby":
                self.ev_lobby(event)
            elif self.state == "recruit":
                self.ev_recruit(event)
            elif self.state == "training_setup":
                self.ev_training_setup(event)
            elif self.state == "matching":
                self.ev_matching(event)
            elif self.state == "result":
                self.ev_result(event)
            elif self.state == "ranking":
                self.ev_ranking(event)
            if self.state == "battle" and self.battle and self.battle.is_training:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F12:
                    self.show_console = not self.show_console
                if self.show_console and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if pygame.Rect(700, 120, 100, 30).collidepoint(mx, my):
                        self.battle.inf_cd = not self.battle.inf_cd
                    elif pygame.Rect(700, 160, 100, 30).collidepoint(mx, my):
                        self.battle.god_mode = not self.battle.god_mode
                    elif pygame.Rect(700, 200, 100, 30).collidepoint(mx, my):
                        self.battle.no_dmg = not self.battle.no_dmg
                    elif pygame.Rect(700, 260, 100, 30).collidepoint(mx, my):
                        self.console_team = 0
                    elif pygame.Rect(810, 260, 100, 30).collidepoint(mx, my):
                        self.console_team = 1
                    else:
                        for i in range(len(ALL_CHARS)):
                            if pygame.Rect(700 + (i % 3) * 90, 320 + (i // 3) * 50, 80, 40).collidepoint(mx, my):
                                self.console_char_idx = i
                                self.battle.pending_spawn = (self.console_team, ALL_CHARS[i])
                        if self.battle.arena.collidepoint(mx, my) and self.battle.pending_spawn:
                            team, ctype = self.battle.pending_spawn
                            self.battle.spawn_fighter(ctype, team, mx, my)

    def ev_login(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.focus = (self.focus + 1) % 2
            elif event.key == pygame.K_BACKSPACE:
                if self.focus == 0:
                    self.username = self.username[:-1]
                elif self.focus == 1:
                    self.password = self.password[:-1]
            elif event.key == pygame.K_RETURN:
                self.do_login()
            elif event.key == pygame.K_ESCAPE:
                self.running = False
        elif event.type == pygame.TEXTINPUT:
            ch = event.text
            if ch and ch.isprintable():
                if self.focus == 0 and len(self.username) < 16:
                    self.username += ch
                elif self.focus == 1 and len(self.password) < 20:
                    self.password += ch
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if pygame.Rect(320, 300, 360, 46).collidepoint(mx, my):
                self.focus = 0
            elif pygame.Rect(320, 372, 360, 46).collidepoint(mx, my):
                self.focus = 1
            elif pygame.Rect(320, 452, 172, 46).collidepoint(mx, my):
                self.do_login()
            elif pygame.Rect(508, 452, 172, 46).collidepoint(mx, my):
                self.do_register()

    def do_login(self):
        u, p = self.username.strip(), self.password
        if not u or not p:
            self.set_msg("不能为空")
            return
        if net.is_online:
            res = net.req("login", {"username": u, "password": p})
            if res.get("success"):
                self.player = res["data"]
                self.player["password_hash"] = p
                self.state = "menu"
                self.set_msg("登录成功", GREEN)
            else:
                self.set_msg(res.get("msg", "失败"))
        else:
            row = self.conn.execute("SELECT * FROM players WHERE username=?", (u,)).fetchone()
            if not row or row["password"] != hash_pw(p):
                self.set_msg("账号或密码错误 (当前为单机模式)")
                return
            self.player = row
            self.state = "menu"
            self.set_msg("本地登录成功", GREEN)

    def do_register(self):
        u, p = self.username.strip(), self.password
        if len(u) < 2 or len(p) < 3:
            self.set_msg("长度不足")
            return
        if net.is_online:
            res = net.req("register", {"username": u, "password": p})
            if res.get("success"):
                self.player = res["data"]
                self.player["password_hash"] = p
                self.state = "menu"
                self.set_msg("注册成功", GREEN)
            else:
                self.set_msg(res.get("msg", "失败"))
        else:
            if self.conn.execute("SELECT id FROM players WHERE username=?", (u,)).fetchone():
                self.set_msg("已存在")
                return
            self.conn.execute("INSERT INTO players (username, password) VALUES (?,?)", (u, hash_pw(p)))
            self.conn.commit()
            self.player = self.conn.execute("SELECT * FROM players WHERE username=?", (u,)).fetchone()
            self.state = "menu"
            self.set_msg("本地注册成功", GREEN)

    def ev_menu(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if pygame.Rect(370, 380, 260, 56).collidepoint(mx, my):
                self.state = "recruit" if net.is_online else "lobby"
                self.lobby_team = [{"is_player": True, "name": self.player["username"], "char": CHAR_FART,
                                    "stars": self.player["stars"]}]
                self.lobby_mode, self.lobby_map = 1, "map1"
                net.room_id = None
            elif pygame.Rect(370, 452, 260, 56).collidepoint(mx, my):
                self.state = "ranking"
                self.rank_tab = 0
            elif pygame.Rect(370, 524, 260, 56).collidepoint(mx, my):
                self.player = None
                self.username = ""
                self.password = ""
                self.state = "login"

    def ev_recruit(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if net.room_id:
                for i in range(len(ALL_CHARS)):
                    if pygame.Rect(30 + (i % 6) * 160, 440 + (i // 6) * 90, 150, 80).collidepoint(mx, my):
                        self.lobby_team[0]["char"] = ALL_CHARS[i]
                        net.req("update_room",
                                {"room_id": net.room_id, "members": self.lobby_team, "mode": self.lobby_mode,
                                 "map": self.lobby_map})
                        return
                for k in (1, 2, 3):
                    if pygame.Rect(180 + (k - 1) * 120, 200, 100, 40).collidepoint(mx, my):
                        self.lobby_mode = k
                        net.req("update_room",
                                {"room_id": net.room_id, "members": self.lobby_team, "mode": self.lobby_mode,
                                 "map": self.lobby_map})
                        return
                for k, key in [(1, "map1"), (2, "map2"), (3, "map3")]:
                    if pygame.Rect(180 + (k - 1) * 120, 260, 110, 40).collidepoint(mx, my):
                        self.lobby_map = key
                        net.req("update_room",
                                {"room_id": net.room_id, "members": self.lobby_team, "mode": self.lobby_mode,
                                 "map": self.lobby_map})
                        return
                if pygame.Rect(780, 620, 180, 56).collidepoint(mx, my):
                    net.req("start_match", {"room_id": net.room_id})
                    self.state = "matching"
                    self.match_time = 0
                    self.match_dots = 0
                if pygame.Rect(30, 620, 120, 40).collidepoint(mx, my):
                    net.req("leave_room", {"room_id": net.room_id})
                    net.room_id = None
                    self.recruit_list = []
            else:
                if pygame.Rect(780, 100, 100, 40).collidepoint(mx, my):
                    res = net.req("get_rooms", {})
                    if res.get("success"):
                        self.recruit_list = res["data"]
                if pygame.Rect(780, 160, 150, 40).collidepoint(mx, my):
                    res = net.req("create_room", {"host": self.player["username"], "members": self.lobby_team})
                    if res.get("success"):
                        net.room_id = res["room_id"]
                for i, room in enumerate(self.recruit_list[:6]):
                    if pygame.Rect(100, 150 + i * 70, 600, 60).collidepoint(mx, my):
                        res = net.req("join_room", {"room_id": room["room_id"], "member": self.lobby_team[0]})
                        if res.get("success"):
                            net.room_id = room["room_id"]
                            self.set_msg("加入成功", GREEN)
                        else:
                            self.set_msg(res.get("msg"))

    def ev_lobby(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i in range(len(ALL_CHARS)):
                if pygame.Rect(30 + (i % 6) * 160, 270 + (i // 6) * 90, 150, 80).collidepoint(mx, my):
                    self.selected_char_idx = i
                    if self.target_member_idx < len(self.lobby_team):
                        self.lobby_team[self.target_member_idx]["char"] = ALL_CHARS[i]
                    return
            max_team = MODES[self.lobby_mode]["per_team"]
            for i in range(max_team):
                if pygame.Rect(70 + i * 200, 60, 160, 90).collidepoint(mx, my):
                    self.target_member_idx = i
                    return
            if pygame.Rect(50, 180, 120, 40).collidepoint(mx, my):
                if self.lobby_map == "map4":
                    self.set_msg("无限训练场只能单人", RED)
                    return
                if len(self.lobby_team) < max_team:
                    if random.random() < 0.75:
                        self.lobby_team.append(
                            {"is_player": False, "name": random.choice(AI_NAMES), "char": random.choice(ALL_CHARS)})
                        self.set_msg("招募成功", GREEN)
                    else:
                        self.set_msg("拒绝", RED)
                return
            for k in (1, 2, 3):
                if pygame.Rect(180 + (k - 1) * 120, 180, 100, 40).collidepoint(mx, my):
                    if self.lobby_map == "map4" and k != 1:
                        self.set_msg("强制单人", RED)
                        return
                    self.lobby_mode = k
                    while len(self.lobby_team) > MODES[k]["per_team"]:
                        self.lobby_team.pop()
                    if self.target_member_idx >= len(self.lobby_team):
                        self.target_member_idx = 0
                    return
            for k, key in [(1, "map1"), (2, "map2"), (3, "map3"), (4, "map4")]:
                if pygame.Rect(180 + (k - 1) * 120, 240, 110, 40).collidepoint(mx, my):
                    self.lobby_map = key
                    if key == "map4":
                        self.lobby_mode = 1
                        self.lobby_team = self.lobby_team[:1]
                        self.target_member_idx = 0
                    return
            if pygame.Rect(780, 620, 180, 56).collidepoint(mx, my):
                if self.lobby_map == "map4":
                    self.state = "training_setup"
                else:
                    self.state = "matching"
                    self.match_time, self.match_dots = 2.2, 0.0
                    self.opp_info = None

    def start_training(self):
        enemy_team = [(random.choice(ALL_CHARS), "假人", "AI", False)] if self.training_has_enemy else []
        self.battle = Battle(self, "map4", 1, [(self.lobby_team[0]["char"], self.lobby_team[0]["name"], "训练", True)],
                             enemy_team, 0)
        self.state = "battle"
        self.show_console = False

    def ev_training_setup(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(300, 350, 180, 56).collidepoint(event.pos):
                self.training_has_enemy = True
                self.start_training()
            elif pygame.Rect(520, 350, 180, 56).collidepoint(event.pos):
                self.training_has_enemy = False
                self.start_training()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "lobby"

    def ev_matching(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "recruit" if net.is_online else "lobby"

    def do_matchmaking(self):
        me = self.player
        per = MODES[self.lobby_mode]["per_team"]
        my_rank = rank_name(me["stars"], me["is_god"])
        player_team = [(m["char"], m["name"], my_rank if m["is_player"] else "队友", m["is_player"]) for m in
                       self.lobby_team]
        enemy_team = [(random.choice(ALL_CHARS), random.choice(AI_NAMES), "对手", False) for _ in range(per)]
        self.opp_info = {"name": enemy_team[0][1], "stars": me["stars"], "is_god": 0, "rank": my_rank, "real": False}
        self.player_team, self.enemy_team, self.difficulty = player_team, enemy_team, 0

    def start_battle(self):
        self.battle = Battle(self, self.lobby_map, self.lobby_mode, self.player_team, self.enemy_team, self.difficulty)
        self.state = "battle"

    def ev_result(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(370, 540, 260, 56).collidepoint(event.pos):
                self.state = "menu"
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
            self.state = "menu"

    def handle_battle_end(self):
        if self.lobby_map == "map4":
            self.state = "menu"
            return
        winner = self.battle.winner
        me = self.player
        old_stars = me["stars"]
        delta = 0
        if net.is_online:
            res = net.req("report_match", {"uid": me["id"], "is_win": winner == 0})
            if res.get("success"):
                new_stars = res["new_stars"]
                delta = new_stars - old_stars
                self.refresh_player()
            else:
                new_stars = old_stars
        else:
            if winner == 0:
                delta = 1
                new_stars = min(109, old_stars + 1)
                self.conn.execute("UPDATE players SET stars=?, wins=wins+1 WHERE id=?", (new_stars, me["id"]))
            elif winner == 1:
                delta = -1
                new_stars = max(0, old_stars - 1)
                self.conn.execute("UPDATE players SET stars=?, losses=losses+1 WHERE id=?", (new_stars, me["id"]))
            self.conn.commit()
            self.refresh_player()
            new_stars = self.player["stars"]
        self.result = {"winner": winner, "delta": delta, "old_stars": old_stars, "new_stars": new_stars,
                       "old_rank": rank_name(old_stars, 0), "new_rank": rank_name(new_stars, self.player["is_god"]),
                       "promoted": False, "opp": self.opp_info}
        self.state = "result"

    def ev_ranking(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(370, 620, 260, 50).collidepoint(event.pos):
                self.state = "menu"
            elif pygame.Rect(360, 118, 135, 40).collidepoint(event.pos):
                self.rank_tab = 0
            elif pygame.Rect(505, 118, 135, 40).collidepoint(event.pos):
                self.rank_tab = 1
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "menu"

    def update(self, dt):
        if self.msg_timer > 0:
            self.msg_timer -= dt
        if self.state == "recruit":
            self.poll_timer += dt
            if self.poll_timer > 1.5:
                self.poll_timer = 0
                if net.room_id:
                    res = net.req("poll_room", {"room_id": net.room_id})
                    if res.get("success"):
                        if res["status"] == "in_game":
                            self.player_team = [(m["char"], m["name"], "队友", m["is_player"]) for m in res["members"]]
                            self.enemy_team = [(m["char"], m["name"], "对手", False) for m in res["opponent"]]
                            self.opp_info = {"name": self.enemy_team[0][1], "stars": self.player["stars"],
                                             "rank": "未知", "is_god": 0}
                            self.lobby_mode = res["mode"]
                            self.lobby_map = res["map"]
                            self.start_battle()
                        else:
                            self.lobby_team = res["members"]
                            self.lobby_mode = res["mode"]
                            self.lobby_map = res["map"]
                    else:
                        net.room_id = None
                        self.set_msg("房间已解散")
                else:
                    res = net.req("get_rooms", {})
                    if res.get("success"):
                        self.recruit_list = res["data"]
        self.sim_timer -= dt
        if self.sim_timer <= 0:
            self.sim_timer = 4.0
            self.simulate_ai_battle()
        if self.state == "matching":
            self.match_dots += dt
            self.match_time -= dt
            if self.match_time <= 0 and self.opp_info is None:
                self.do_matchmaking()
                self.match_time = 0.9
            elif self.opp_info is not None and self.match_time <= 0:
                self.start_battle()
        elif self.state == "battle" and self.battle:
            self.battle.update(dt)
            if self.battle.finished and not self.battle.is_training and self.battle.end_timer > 1.6:
                self.handle_battle_end()

    def draw(self):
        self.screen.fill(BG)
        if self.state == "login":
            self.draw_login()
        elif self.state == "menu":
            self.draw_menu()
        elif self.state == "lobby":
            self.draw_lobby()
        elif self.state == "recruit":
            self.draw_recruit()
        elif self.state == "training_setup":
            self.draw_training_setup()
        elif self.state == "matching":
            self.draw_matching()
        elif self.state == "battle" and self.battle:
            self.battle.draw(self.screen)
            if self.battle.is_training and self.show_console:
                self.draw_console()
        elif self.state == "result":
            self.draw_result()
        elif self.state == "ranking":
            self.draw_ranking()
        if self.msg_timer > 0 and self.msg:
            img = get_font(18, True).render(self.msg, True, self.msg_color)
            box = pygame.Rect(0, 0, img.get_width() + 28, img.get_height() + 14)
            box.center = (WIDTH // 2, 60)
            s = pygame.Surface(box.size, pygame.SRCALPHA)
            s.fill((10, 12, 20, 210))
            self.screen.blit(s, box.topleft)
            self.screen.blit(img, (box.x + 14, box.y + 7))

    def draw_login(self):
        draw_text(self.screen, "段位大乱斗", get_font(48, True), ACCENT, (WIDTH // 2, 130), center=True)

        # 核心改动：不再显示IP输入框，自动判断状态
        if net.is_connecting:
            status_text = "正在自动连接服务器 (%d/5)..." % net.connect_attempts
            status_color = YELLOW
        elif net.is_online:
            status_text = "当前模式: 正式服 (已连接)"
            status_color = GREEN
        else:
            status_text = "当前模式: 单机模式 (连接失败)"
            status_color = ORANGE

        draw_text(self.screen, status_text, get_font(18, True), status_color, (WIDTH // 2, 180), center=True)

        draw_text(self.screen, "用户名", get_font(17), TEXT_DIM, (320, 276))
        r_name = pygame.Rect(320, 300, 360, 46)
        draw_panel(self.screen, r_name, PANEL2, radius=8, border=ACCENT if self.focus == 0 else (70, 76, 100))
        draw_text(self.screen,
                  self.username + ("|" if self.focus == 0 and int(pygame.time.get_ticks() / 400) % 2 == 0 else ""),
                  get_font(20), TEXT, (r_name.x + 14, r_name.centery - 12))

        draw_text(self.screen, "密码", get_font(17), TEXT_DIM, (320, 348))
        r_pw = pygame.Rect(320, 372, 360, 46)
        draw_panel(self.screen, r_pw, PANEL2, radius=8, border=ACCENT if self.focus == 1 else (70, 76, 100))
        draw_text(self.screen, "*" * len(self.password) + (
            "|" if self.focus == 1 and int(pygame.time.get_ticks() / 400) % 2 == 0 else ""), get_font(20), TEXT,
                  (r_pw.x + 14, r_pw.centery - 12))

        draw_button(self.screen, pygame.Rect(320, 452, 172, 46), "登  录", get_font(20, True), self.mouse_pos, ACCENT)
        draw_button(self.screen, pygame.Rect(508, 452, 172, 46), "注  册", get_font(20, True), self.mouse_pos, ACCENT2)

    # ... (以下所有 draw_menu, draw_recruit, draw_lobby, draw_training_setup, draw_console, draw_matching, draw_result, draw_ranking 等均保持原样，不予删减)

    def draw_menu(self):
        me = self.player
        draw_text(self.screen, "段位大乱斗", get_font(38, True), ACCENT, (WIDTH // 2, 70), center=True)
        draw_panel(self.screen, pygame.Rect(230, 130, 540, 210), PANEL, radius=16, border=ACCENT)
        draw_text(self.screen, display_name(me["username"]), get_font(22, True), TEXT, (260, 155))
        draw_text(self.screen, rank_name(me["stars"], me["is_god"]), get_font(30, True),
                  rank_color(me["stars"], me["is_god"]), (260, 192))
        draw_text(self.screen, "总场次 %d  胜 %d  负 %d" % (me["wins"] + me["losses"], me["wins"], me["losses"]),
                  get_font(17), TEXT_DIM, (260, 250))
        draw_button(self.screen, pygame.Rect(370, 380, 260, 56), "开始匹配", get_font(21, True), self.mouse_pos, ACCENT)
        draw_button(self.screen, pygame.Rect(370, 452, 260, 56), "排行榜", get_font(21, True), self.mouse_pos, ACCENT2)
        draw_button(self.screen, pygame.Rect(370, 524, 260, 56), "退出登录", get_font(21, True), self.mouse_pos,
                    (140, 150, 180))

    def draw_recruit(self):
        draw_text(self.screen, "招募大厅", get_font(36, True), ACCENT, (WIDTH // 2, 40), center=True)
        if net.room_id:
            draw_text(self.screen, "我的房间 (等待加入...)", get_font(20, True), TEXT, (50, 90))
            for i in range(MODES[self.lobby_mode]["per_team"]):
                rect = pygame.Rect(70 + i * 200, 130, 160, 90)
                if i < len(self.lobby_team):
                    m = self.lobby_team[i]
                    info = CHAR_INFO[m["char"]]
                    draw_panel(self.screen, rect, PANEL2, radius=10, border=info["color"])
                    draw_text(self.screen, m["name"], get_font(16, True), TEXT, (rect.centerx, rect.y + 20),
                              center=True)
                    draw_text(self.screen, info["name"], get_font(13), info["color"], (rect.centerx, rect.y + 50),
                              center=True)
                else:
                    draw_panel(self.screen, rect, (24, 26, 40), radius=10, border=(60, 64, 80))
                    draw_text(self.screen, "等待玩家...", get_font(15), TEXT_DIM, (rect.centerx, rect.centery),
                              center=True)
            draw_text(self.screen, "模式:", get_font(16), TEXT_DIM, (150, 210))
            for k in (1, 2, 3):
                rect = pygame.Rect(200 + (k - 1) * 120, 200, 100, 40)
                draw_panel(self.screen, rect, ACCENT if self.lobby_mode == k else PANEL2, radius=8)
                draw_text(self.screen, MODES[k]["name"], get_font(15, True), TEXT, rect.center, center=True)
            draw_text(self.screen, "地图:", get_font(16), TEXT_DIM, (150, 260))
            for k, key in [(1, "map1"), (2, "map2"), (3, "map3")]:
                rect = pygame.Rect(200 + (k - 1) * 120, 250, 110, 40)
                draw_panel(self.screen, rect, ACCENT if self.lobby_map == key else PANEL2, radius=8)
                draw_text(self.screen, MAPS[key]["name"], get_font(15, True), TEXT, rect.center, center=True)
            for i, ctype in enumerate(ALL_CHARS):
                rect = pygame.Rect(30 + (i % 6) * 160, 440 + (i // 6) * 90, 150, 80)
                info = CHAR_INFO[ctype]
                draw_panel(self.screen, rect, PANEL2 if self.lobby_team[0]["char"] == ctype else PANEL, radius=10,
                           border=info["color"])
                draw_text(self.screen, info["name"], get_font(14, True), TEXT, (rect.centerx, rect.y + 30), center=True)
            draw_button(self.screen, pygame.Rect(30, 620, 120, 40), "离开房间", get_font(16, True), self.mouse_pos, RED)
            draw_button(self.screen, pygame.Rect(780, 620, 180, 56), "开始匹配", get_font(22, True), self.mouse_pos,
                        ACCENT, enabled=True)
        else:
            draw_button(self.screen, pygame.Rect(780, 100, 100, 40), "刷新", get_font(16, True), self.mouse_pos, ACCENT)
            draw_button(self.screen, pygame.Rect(780, 160, 150, 40), "发布招募", get_font(16, True), self.mouse_pos,
                        GREEN)
            draw_text(self.screen, "可加入的队伍:", get_font(18, True), TEXT, (100, 110))
            if not self.recruit_list:
                draw_text(self.screen, "暂无队伍，你可以自己发布一个！", get_font(16), TEXT_DIM, (100, 180))
            for i, room in enumerate(self.recruit_list[:6]):
                rect = pygame.Rect(100, 150 + i * 70, 600, 60)
                draw_panel(self.screen, rect, PANEL2, radius=10, border=(70, 76, 100))
                draw_text(self.screen, "房主: %s" % room["host"], get_font(16, True), TEXT, (rect.x + 20, rect.y + 20))
                draw_text(self.screen, "人数: %d/%d" % (room["count"], MODES[room["mode"]]["per_team"]), get_font(14),
                          ACCENT, (rect.right - 150, rect.y + 22))
                draw_button(self.screen, pygame.Rect(rect.right - 100, rect.y + 10, 80, 40), "加入", get_font(14, True),
                            self.mouse_pos, GREEN)

    def draw_lobby(self):
        max_team = MODES[self.lobby_mode]["per_team"]
        draw_text(self.screen, "单机组队配置", get_font(20, True), TEXT, (50, 25))
        for i in range(max_team):
            rect = pygame.Rect(70 + i * 200, 60, 160, 90)
            if i < len(self.lobby_team):
                m = self.lobby_team[i]
                info = CHAR_INFO[m["char"]]
                draw_panel(self.screen, rect, PANEL2, radius=10,
                           border=info["color"] if i == self.target_member_idx else (70, 76, 100))
                draw_text(self.screen, m["name"], get_font(16, True), TEXT, (rect.centerx, rect.y + 20), center=True)
                draw_text(self.screen, info["name"], get_font(13), info["color"], (rect.centerx, rect.y + 50),
                          center=True)
            else:
                draw_panel(self.screen, rect, (24, 26, 40), radius=10, border=(60, 64, 80))
                draw_text(self.screen, "空位", get_font(16), TEXT_DIM, (rect.centerx, rect.centery), center=True)
        draw_button(self.screen, pygame.Rect(50, 180, 120, 40), "招募人机", get_font(16, True), self.mouse_pos, GREEN,
                    enabled=(len(self.lobby_team) < max_team and self.lobby_map != "map4"))
        draw_text(self.screen, "模式:", get_font(16), TEXT_DIM, (150, 190))
        for k in (1, 2, 3):
            rect = pygame.Rect(200 + (k - 1) * 110, 180, 100, 40)
            draw_panel(self.screen, rect, ACCENT if self.lobby_mode == k else PANEL2, radius=8)
            draw_text(self.screen, MODES[k]["name"], get_font(15, True), TEXT, rect.center, center=True)
        draw_text(self.screen, "地图:", get_font(16), TEXT_DIM, (150, 240))
        for k, key in [(1, "map1"), (2, "map2"), (3, "map3"), (4, "map4")]:
            rect = pygame.Rect(180 + (k - 1) * 120, 230, 110, 40)
            draw_panel(self.screen, rect, ACCENT if self.lobby_map == key else PANEL2, radius=8)
            draw_text(self.screen, MAPS[key]["name"], get_font(15, True), TEXT, rect.center, center=True)
        for i, ctype in enumerate(ALL_CHARS):
            rect = pygame.Rect(30 + (i % 6) * 160, 270 + (i // 6) * 90, 150, 80)
            info = CHAR_INFO[ctype]
            draw_panel(self.screen, rect, PANEL2 if self.selected_char_idx == i else PANEL, radius=10,
                       border=info["color"] if self.selected_char_idx == i else (70, 76, 100))
            draw_text(self.screen, info["name"], get_font(14, True), TEXT, (rect.centerx, rect.y + 30), center=True)
        draw_button(self.screen, pygame.Rect(780, 620, 180, 56), "开始匹配", get_font(22, True), self.mouse_pos, ACCENT)

    def draw_training_setup(self):
        draw_text(self.screen, "进入无限训练场", get_font(38, True), GREEN, (WIDTH // 2, 150), center=True)
        draw_button(self.screen, pygame.Rect(300, 350, 180, 56), "生成敌人", get_font(22, True), self.mouse_pos, RED)
        draw_button(self.screen, pygame.Rect(520, 350, 180, 56), "空场练习", get_font(22, True), self.mouse_pos, GREEN)
        draw_text(self.screen, "进入后按 F12 呼出控制台", get_font(16), YELLOW, (WIDTH // 2, 460), center=True)

    def draw_console(self):
        panel = pygame.Rect(680, 100, 300, 500)
        draw_panel(self.screen, panel, (20, 24, 38), radius=12, border=ACCENT)
        draw_text(self.screen, "训练控制台", get_font(20, True), ACCENT, (panel.centerx, panel.y + 20), center=True)

        def draw_toggle(x, y, text, active):
            draw_panel(self.screen, pygame.Rect(x, y, 100, 30), (40, 80, 60) if active else (80, 40, 40), radius=6)
            draw_text(self.screen, text, get_font(14, True), GREEN if active else RED, (x + 50, y + 15), center=True)

        draw_toggle(700, 120, "无冷却", self.battle.inf_cd)
        draw_toggle(700, 160, "无敌", self.battle.god_mode)
        draw_toggle(700, 200, "不扣血", self.battle.no_dmg)
        draw_panel(self.screen, pygame.Rect(700, 260, 100, 30), ACCENT if self.console_team == 0 else PANEL2, radius=6)
        draw_text(self.screen, "我方", get_font(14, True), TEXT, (750, 275), center=True)
        draw_panel(self.screen, pygame.Rect(810, 260, 100, 30), RED if self.console_team == 1 else PANEL2, radius=6)
        draw_text(self.screen, "敌方", get_font(14, True), TEXT, (860, 275), center=True)
        for i, ctype in enumerate(ALL_CHARS):
            bx, by = 700 + (i % 3) * 90, 320 + (i // 3) * 50
            draw_panel(self.screen, pygame.Rect(bx, by, 80, 40), ACCENT if self.console_char_idx == i else PANEL2,
                       radius=6)
            draw_text(self.screen, CHAR_INFO[ctype]["name"][:4], get_font(12, True), TEXT, (bx + 40, by + 20),
                      center=True)

    def draw_matching(self):
        draw_text(self.screen, "正在匹配对手...", get_font(34, True), ACCENT, (WIDTH // 2, 200), center=True)
        t = pygame.time.get_ticks() / 1000.0
        for i in range(12):
            ang = t * 2 + i * math.pi / 6
            alpha = 60 + int(180 * (i / 12))
            pygame.draw.circle(self.screen,
                               (ACCENT[0] * alpha // 255, ACCENT[1] * alpha // 255, ACCENT[2] * alpha // 255),
                               (int(WIDTH // 2 + math.cos(ang) * 60), int(310 + math.sin(ang) * 60)), 6)
        draw_text(self.screen, "地图：%s   模式：%s" % (MAPS[self.lobby_map]["name"], MODES[self.lobby_mode]["name"]),
                  get_font(17), TEXT_DIM, (WIDTH // 2, 446), center=True)

    def draw_result(self):
        r = self.result
        txt, col = ("胜  利", GREEN) if r["winner"] == 0 else (
            ("失  败", RED) if r["winner"] == 1 else ("平  局", TEXT_DIM))
        draw_text(self.screen, txt, get_font(50, True), col, (WIDTH // 2, 110), center=True)
        card = pygame.Rect(240, 180, 520, 320)
        draw_panel(self.screen, card, PANEL, radius=16, border=col)
        draw_text(self.screen, "对手：%s" % r["opp"]["name"], get_font(22, True), TEXT, (card.x + 30, card.y + 24))
        draw_text(self.screen, "段位变化", get_font(17), TEXT_DIM, (card.x + 30, card.y + 114))
        draw_text(self.screen, r["old_rank"], get_font(22, True), TEXT_DIM, (card.x + 30, card.y + 142))
        draw_text(self.screen, "→", get_font(22, True), TEXT_DIM, (card.centerx, card.y + 142), center=True)
        draw_text(self.screen, r["new_rank"], get_font(22, True), rank_color(r["new_stars"], 0),
                  (card.x + 30, card.y + 178))
        delta_txt = ("+%d 星" % r["delta"]) if r["delta"] > 0 else (
            ("%d 星" % r["delta"]) if r["delta"] < 0 else "±0 星")
        draw_text(self.screen, delta_txt, get_font(22, True),
                  GREEN if r["delta"] > 0 else (RED if r["delta"] < 0 else TEXT_DIM), (card.right - 30, card.y + 178),
                  right=True)
        draw_button(self.screen, pygame.Rect(370, 540, 260, 56), "返回主菜单", get_font(21, True), self.mouse_pos,
                    ACCENT)

    def draw_ranking(self):
        draw_text(self.screen, "排  行  榜", get_font(32, True), GOLD, (WIDTH // 2, 70), center=True)
        draw_button(self.screen, pygame.Rect(360, 118, 135, 40), "超王榜", get_font(17, True), self.mouse_pos, ACCENT,
                    enabled=(self.rank_tab == 0))
        draw_button(self.screen, pygame.Rect(505, 118, 135, 40), "战神榜", get_font(17, True), self.mouse_pos, GOLD,
                    enabled=(self.rank_tab == 1))
        if net.is_online:
            res = net.req("get_ranking", {"tab": self.rank_tab})
            rows = res.get("data", []) if res.get("success") else []
        else:
            if self.rank_tab == 0:
                rows = self.conn.execute(
                    "SELECT * FROM players WHERE is_god=0 AND stars >= ? ORDER BY stars DESC LIMIT 10",
                    (RANK_QUALIFY,)).fetchall()
            else:
                rows = self.conn.execute("SELECT * FROM players WHERE is_god=1 ORDER BY stars DESC LIMIT 10").fetchall()
        panel = pygame.Rect(150, 210, 700, 380)
        draw_panel(self.screen, panel, PANEL, radius=14, border=(70, 76, 100))
        for i, row in enumerate(rows):
            y = panel.y + 58 + i * 32
            draw_text(self.screen, "#%d" % (i + 1), get_font(17, True), GOLD if i == 0 else TEXT_DIM, (panel.x + 26, y))
            draw_text(self.screen, display_name(row["username"]), get_font(18, True), TEXT, (panel.x + 110, y - 2))
            draw_text(self.screen, rank_name(row["stars"], row["is_god"]), get_font(15),
                      rank_color(row["stars"], row["is_god"]), (panel.x + 380, y + 1))
            draw_text(self.screen, "%d / %d" % (row["wins"], row["losses"]), get_font(15), TEXT_DIM,
                      (panel.x + 560, y + 1))
        draw_button(self.screen, pygame.Rect(370, 632, 260, 48), "返回主菜单", get_font(20, True), self.mouse_pos,
                    ACCENT)


def main():
    pygame.init()
    pygame.key.start_text_input()
    init_local_db()
    game = Game()
    game.run()


if __name__ == "__main__":
    main()