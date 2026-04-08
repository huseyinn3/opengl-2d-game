"""
Ates ve Su - Tapinak Macerasi
Pygame + OpenGL ile 2D platform oyunu

Kontroller:
  Ates  -> W (zipla), A/D (hareket)
  Su    -> Yukari ok (zipla), Sol/Sag ok (hareket)
  R     -> Yeniden baslat
  ESC   -> Cikis
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import time
import array
import struct
import random

# pencere ve fps ayarlari
WIDTH, HEIGHT = 1050, 700
FPS = 60

# renk paleti
COLORS = {
    # arka plan
    'bg_brick': (0.70, 0.62, 0.35),
    'bg_brick_line': (0.55, 0.48, 0.25),
    
    # platform renkleri
    'platform': (0.24, 0.22, 0.18),
    'platform_light': (0.30, 0.27, 0.22),
    'platform_line': (0.15, 0.13, 0.10),
    
    # karakter renkleri
    'fire_body': (1.0, 0.35, 0.0),
    'fire_light': (1.0, 0.6, 0.1),
    'fire_dark': (0.85, 0.2, 0.0),
    'water_body': (0.2, 0.5, 1.0),
    'water_light': (0.5, 0.75, 1.0),
    'water_dark': (0.1, 0.3, 0.7),
    
    # elmas renkleri
    'gem_red': (1.0, 0.0, 0.0),
    'gem_red_light': (1.0, 0.5, 0.5),
    'gem_blue': (0.0, 0.6, 1.0),
    'gem_blue_light': (0.5, 0.8, 1.0),
    
    # tehlike renkleri
    'lava': (1.0, 0.4, 0.0),
    'lava_bright': (1.0, 0.6, 0.2),
    'water_pool': (0.0, 0.55, 0.95),
    'water_pool_bright': (0.3, 0.75, 1.0),
    'poison': (0.4, 0.8, 0.2),
    'poison_bright': (0.6, 1.0, 0.4),
    
    # diger
    'door_frame': (0.35, 0.28, 0.18),
    'door_fire': (0.6, 0.2, 0.1),
    'door_water': (0.1, 0.35, 0.55),
    'button_purple': (0.6, 0.2, 0.6),
    'lever_yellow': (0.85, 0.75, 0.2),
    'box_gray': (0.5, 0.5, 0.5),
    'elevator': (0.75, 0.7, 0.8),
    'plant_green': (0.2, 0.55, 0.15),
    'plant_dark': (0.15, 0.4, 0.1),
    'vine_green': (0.25, 0.6, 0.2),
}





def create_pygame_sound_from_samples(samples, sample_rate=44100):
    # sample listesinden pygame Sound olustur
    # 16-bit stereo PCM formatında buffer oluştur
    buf = array.array('h')  # signed short (16-bit)
    for sample in samples:
        # Clamp değeri -32767 ile 32767 arasında
        val = int(max(-32767, min(32767, sample * 32767)))
        buf.append(val)  # Sol kanal
        buf.append(val)  # Sağ kanal
    
    sound = pygame.mixer.Sound(buffer=buf)
    return sound

def create_gem_collect_sound():
    # kisa arpej sesi
    sample_rate = 44100
    duration = 0.15
    n_samples = int(sample_rate * duration)
    samples = [0.0] * n_samples
    
    # yukselen notalar
    freqs = [880, 1100, 1320]  # A5, C#6, E6
    
    for i, freq in enumerate(freqs):
        start = int(i * n_samples / 4)
        end = min(start + int(n_samples / 2), n_samples)
        seg_len = end - start
        
        for j in range(seg_len):
            t = j / sample_rate
            # sinus dalga
            val = math.sin(2 * math.pi * freq * t) * 0.3
            
            # zarf
            env = 1.0
            attack_len = int(seg_len * 0.1)
            release_len = int(seg_len * 0.5)
            
            if j < attack_len:
                env = j / attack_len
            elif j > seg_len - release_len:
                env = (seg_len - j) / release_len
            
            samples[start + j] += val * env
    
    return create_pygame_sound_from_samples(samples, sample_rate)

def create_death_sound():
    # dusen tonlu olum sesi
    sample_rate = 44100
    duration = 0.4
    n_samples = int(sample_rate * duration)
    samples = [0.0] * n_samples
    
    freq_start = 400
    freq_end = 100
    
    for i in range(n_samples):
        t = i / sample_rate
        # Düşen frekans
        freq = freq_start - (freq_start - freq_end) * i / n_samples
        
        # ana dalga
        val = math.sin(2 * math.pi * freq * t) * 0.5
        
        # biraz gurultu ekle
        val += random.uniform(-0.1, 0.1)
        
        # zarf - release
        release_start = int(n_samples * 0.6)
        if i > release_start:
            env = (n_samples - i) / (n_samples - release_start)
            val *= env
        
        samples[i] = val * 0.6
    
    return create_pygame_sound_from_samples(samples, sample_rate)

def create_win_sound():
    # zafer melodisi
    sample_rate = 44100
    duration = 0.8
    n_samples = int(sample_rate * duration)
    samples = [0.0] * n_samples
    
    # zafer melodisi
    notes = [
        (523, 0.0, 0.2),   # C5
        (659, 0.15, 0.2),  # E5
        (784, 0.3, 0.2),   # G5
        (1047, 0.45, 0.35) # C6
    ]
    
    for freq, start_time, dur in notes:
        start = int(start_time * sample_rate)
        seg_len = int(dur * sample_rate)
        end = min(start + seg_len, n_samples)
        
        for j in range(end - start):
            t = j / sample_rate
            # ana dalga + harmonik
            val = math.sin(2 * math.pi * freq * t) * 0.3
            val += math.sin(2 * math.pi * freq * 2 * t) * 0.1
            
            # zarf
            env = 1.0
            attack_len = int(seg_len * 0.1)
            release_len = int(seg_len * 0.4)
            
            if j < attack_len:
                env = j / attack_len
            elif j > seg_len - release_len:
                env = (seg_len - j) / release_len
            
            samples[start + j] += val * env
    
    return create_pygame_sound_from_samples(samples, sample_rate)

def create_background_music():
    # dongusel arka plan muzigi
    sample_rate = 44100
    duration = 4.0  # 4 saniyelik döngü
    n_samples = int(sample_rate * duration)
    samples = [0.0] * n_samples
    
    # bas notalari
    bass_notes = [
        (65, 0.0), (65, 0.5), (82, 1.0), (82, 1.5),
        (55, 2.0), (55, 2.5), (73, 3.0), (73, 3.5)
    ]
    
    for freq, start_time in bass_notes:
        start = int(start_time * sample_rate)
        note_dur = 0.45
        seg_len = int(note_dur * sample_rate)
        end = min(start + seg_len, n_samples)
        
        for j in range(end - start):
            t = j / sample_rate
            # bas
            val = math.sin(2 * math.pi * freq * t) * 0.12
            val += math.sin(2 * math.pi * freq * 0.5 * t) * 0.08
            
            # zarf
            env = 1.0
            attack_len = int(seg_len * 0.05)
            release_len = int(seg_len * 0.3)
            
            if j < attack_len and attack_len > 0:
                env = j / attack_len
            elif j > seg_len - release_len and release_len > 0:
                env = (seg_len - j) / release_len
            
            samples[start + j] += val * env
    
    # pad ses
    pad_freq = 130
    for i in range(n_samples):
        t = i / sample_rate
        # LFO
        lfo = math.sin(2 * math.pi * 0.3 * t) * 0.3 + 0.7
        
        val = math.sin(2 * math.pi * pad_freq * t) * 0.04 * lfo
        val += math.sin(2 * math.pi * pad_freq * 1.5 * t) * 0.02 * lfo
        
        samples[i] += val
    
    # melodi
    melody = [
        (262, 0.25, 0.2), (294, 0.75, 0.2), (262, 1.25, 0.2), (247, 1.75, 0.3),
        (262, 2.25, 0.2), (330, 2.75, 0.2), (294, 3.25, 0.2), (262, 3.75, 0.2)
    ]
    
    for freq, start_time, dur in melody:
        start = int(start_time * sample_rate)
        seg_len = int(dur * sample_rate)
        end = min(start + seg_len, n_samples)
        
        for j in range(end - start):
            t = j / sample_rate
            val = math.sin(2 * math.pi * freq * t) * 0.06
            
            # zarf
            env = 1.0
            attack_len = int(seg_len * 0.1)
            release_len = int(seg_len * 0.5)
            
            if j < attack_len and attack_len > 0:
                env = j / attack_len
            elif j > seg_len - release_len and release_len > 0:
                env = (seg_len - j) / release_len
            
            samples[start + j] += val * env
    
    # normalize et
    max_val = max(abs(s) for s in samples) if samples else 1
    if max_val > 0:
        samples = [s / max_val * 0.35 for s in samples]
    
    return create_pygame_sound_from_samples(samples, sample_rate)



# -- yardimci fonksiyonlar --

def draw_rect(x, y, w, h, color):
    # duz dikdortgen
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()

def draw_rect_gradient_v(x, y, w, h, color_bottom, color_top):
    # dikey gradient
    glBegin(GL_QUADS)
    glColor3f(*color_bottom)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glColor3f(*color_top)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()

def check_rect_collision(x1, y1, w1, h1, x2, y2, w2, h2):
    # AABB carpisma testi
    return (x1 < x2 + w2 and x1 + w1 > x2 and
            y1 < y2 + h2 and y1 + h1 > y2)



# -- Platform --

class Platform:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def draw(self):
        # Ana gövde
        draw_rect(self.x, self.y, self.width, self.height, COLORS['platform'])
        
        # Üst kenar vurgusu
        draw_rect(self.x, self.y + self.height - 3, 
                  self.width, 3, COLORS['platform_light'])
        
        # Tuğla çizgileri
        glColor3f(*COLORS['platform_line'])
        glLineWidth(1)
        
        brick_h = 12
        brick_w = 24
        
        for row in range(int(self.height / brick_h) + 1):
            y_pos = self.y + row * brick_h
            if y_pos <= self.y + self.height:
                glBegin(GL_LINES)
                glVertex2f(self.x, y_pos)
                glVertex2f(self.x + self.width, y_pos)
                glEnd()
            
            offset = (brick_w / 2) if row % 2 == 1 else 0
            for col in range(int(self.width / brick_w) + 2):
                x_pos = self.x + col * brick_w - offset
                if self.x <= x_pos <= self.x + self.width:
                    y_end = min(y_pos + brick_h, self.y + self.height)
                    if y_pos < self.y + self.height:
                        glBegin(GL_LINES)
                        glVertex2f(x_pos, y_pos)
                        glVertex2f(x_pos, y_end)
                        glEnd()
    
    def get_rect(self):
        return (self.x, self.y, self.width, self.height)



# -- Hareketli Platform --

class MovingPlatform:
    def __init__(self, x, y, width, height, move_type='horizontal', 
                 min_pos=0, max_pos=100, speed=2):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.move_type = move_type  # 'horizontal' veya 'vertical'
        self.min_pos = min_pos
        self.max_pos = max_pos
        self.speed = speed
        self.direction = 1  # 1: sağa/yukarı, -1: sola/aşağı
    
    def update(self):
        if self.move_type == 'horizontal':
            self.x += self.speed * self.direction
            if self.x >= self.max_pos:
                self.x = self.max_pos
                self.direction = -1
            elif self.x <= self.min_pos:
                self.x = self.min_pos
                self.direction = 1
        else:  # vertical
            self.y += self.speed * self.direction
            if self.y >= self.max_pos:
                self.y = self.max_pos
                self.direction = -1
            elif self.y <= self.min_pos:
                self.y = self.min_pos
                self.direction = 1
    
    def draw(self):
        # Farklı renk - hareketli olduğu belli olsun
        glColor3f(0.35, 0.30, 0.25)
        glBegin(GL_QUADS)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.width, self.y)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x, self.y + self.height)
        glEnd()
        
        # Üst kenar - parlak
        glColor3f(0.45, 0.40, 0.35)
        glBegin(GL_QUADS)
        glVertex2f(self.x, self.y + self.height - 3)
        glVertex2f(self.x + self.width, self.y + self.height - 3)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x, self.y + self.height)
        glEnd()
        
        # Kenar çizgisi
        glColor3f(0.5, 0.45, 0.35)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.width, self.y)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x, self.y + self.height)
        glEnd()
        
        # Ok işaretleri (hareket yönünü göster)
        glColor3f(0.6, 0.55, 0.45)
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        
        if self.move_type == 'horizontal':
            # Sol ok
            glBegin(GL_TRIANGLES)
            glVertex2f(self.x + 8, cy)
            glVertex2f(self.x + 15, cy + 4)
            glVertex2f(self.x + 15, cy - 4)
            glEnd()
            
            # Sağ ok
            glBegin(GL_TRIANGLES)
            glVertex2f(self.x + self.width - 8, cy)
            glVertex2f(self.x + self.width - 15, cy + 4)
            glVertex2f(self.x + self.width - 15, cy - 4)
            glEnd()
        else:  # vertical
            # Yukarı ok
            glBegin(GL_TRIANGLES)
            glVertex2f(cx, self.y + self.height - 4)
            glVertex2f(cx - 5, self.y + self.height - 10)
            glVertex2f(cx + 5, self.y + self.height - 10)
            glEnd()
            
            # Aşağı ok
            glBegin(GL_TRIANGLES)
            glVertex2f(cx, self.y + 4)
            glVertex2f(cx - 5, self.y + 10)
            glVertex2f(cx + 5, self.y + 10)
            glEnd()
    
    def get_rect(self):
        return (self.x, self.y, self.width, self.height)



# -- Oyuncu (Player) --

class Player:
    def __init__(self, x, y, player_type, controls):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.width = 24
        self.height = 30
        self.player_type = player_type
        self.controls = controls
        
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 4.0
        self.jump_power = 9.5
        self.gravity = 0.4
        self.on_ground = False
        
        self.is_dead = False
        self.reached_door = False
        self.facing_right = True
    
    def handle_input(self, keys):
        if self.is_dead:
            return
        
        self.vel_x = 0
        
        if keys[self.controls['left']]:
            self.vel_x = -self.speed
            self.facing_right = False
        if keys[self.controls['right']]:
            self.vel_x = self.speed
            self.facing_right = True
        if keys[self.controls['jump']] and self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
    
    def update(self, platforms, elevators, box, moving_platforms=None):
        if self.is_dead:
            return
        
        # Hangi hareketli platformda olduğumuzu takip et
        on_moving_platform = None
        
        # Hareketli platformda mıyız? (platform ile birlikte hareket)
        if moving_platforms and self.on_ground:
            for mp in moving_platforms:
                # Karakterin ayakları platformun üstünde mi?
                if (self.x + self.width > mp.x and self.x < mp.x + mp.width and
                    abs(self.y - (mp.y + mp.height)) < 5):
                    on_moving_platform = mp
                    if mp.move_type == 'horizontal':
                        self.x += mp.speed * mp.direction
                    else:  # vertical
                        self.y += mp.speed * mp.direction
                    break
        
        # Yerçekimi
        self.vel_y -= self.gravity
        
        # Yatay hareket
        self.x += self.vel_x
        
        # Yatay çarpışma - platformlar
        for plat in platforms:
            if check_rect_collision(self.x, self.y, self.width, self.height,
                                    *plat.get_rect()):
                if self.vel_x > 0:
                    self.x = plat.x - self.width
                elif self.vel_x < 0:
                    self.x = plat.x + plat.width
        
        # Yatay çarpışma - hareketli platformlar
        if moving_platforms:
            for mp in moving_platforms:
                if check_rect_collision(self.x, self.y, self.width, self.height,
                                        mp.x, mp.y, mp.width, mp.height):
                    if self.vel_x > 0:
                        self.x = mp.x - self.width
                    elif self.vel_x < 0:
                        self.x = mp.x + mp.width
        
        # Yatay çarpışma - asansörler
        for elev in elevators:
            if check_rect_collision(self.x, self.y, self.width, self.height,
                                    elev.x, elev.y, elev.width, elev.height):
                if self.vel_x > 0:
                    self.x = elev.x - self.width
                elif self.vel_x < 0:
                    self.x = elev.x + elev.width
        
        # Yatay çarpışma - kutu
        if box and check_rect_collision(self.x, self.y, self.width, self.height,
                                        box.x, box.y, box.size, box.size):
            if self.vel_x > 0:
                # Kutuyu it
                box.push(self.vel_x, platforms)
                if check_rect_collision(self.x, self.y, self.width, self.height,
                                        box.x, box.y, box.size, box.size):
                    self.x = box.x - self.width
            elif self.vel_x < 0:
                box.push(self.vel_x, platforms)
                if check_rect_collision(self.x, self.y, self.width, self.height,
                                        box.x, box.y, box.size, box.size):
                    self.x = box.x + box.size
        
        # Dikey hareket
        self.y += self.vel_y
        self.on_ground = False
        
        # Dikey çarpışma - platformlar
        for plat in platforms:
            if check_rect_collision(self.x, self.y, self.width, self.height,
                                    *plat.get_rect()):
                if self.vel_y < 0:
                    self.y = plat.y + plat.height
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y > 0:
                    self.y = plat.y - self.height
                    self.vel_y = 0
        
        # Dikey çarpışma - hareketli platformlar
        if moving_platforms:
            for mp in moving_platforms:
                if check_rect_collision(self.x, self.y, self.width, self.height,
                                        mp.x, mp.y, mp.width, mp.height):
                    # Yukarıdan iniyorsak (düşüyorsak) - platforma in
                    if self.vel_y < 0:
                        self.y = mp.y + mp.height
                        self.vel_y = 0
                        self.on_ground = True
                    # Aşağıdan çarpıyorsak (zıplarken) - sadece platform aşağı gitmiyorsa
                    elif self.vel_y > 0:
                        # Dikey platformda yukarı zıplarken çarpışma kontrolü
                        if mp.move_type == 'vertical' and mp.direction > 0:
                            # Platform yukarı gidiyor ve biz zıplıyoruz - geç
                            pass
                        else:
                            self.y = mp.y - self.height
                            self.vel_y = 0
        
        # Dikey çarpışma - asansörler
        for elev in elevators:
            if check_rect_collision(self.x, self.y, self.width, self.height,
                                    elev.x, elev.y, elev.width, elev.height):
                if self.vel_y < 0:
                    self.y = elev.y + elev.height
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y > 0:
                    self.y = elev.y - self.height
                    self.vel_y = 0
        
        # Dikey çarpışma - kutu
        if box and check_rect_collision(self.x, self.y, self.width, self.height,
                                        box.x, box.y, box.size, box.size):
            if self.vel_y < 0:
                self.y = box.y + box.size
                self.vel_y = 0
                self.on_ground = True
            elif self.vel_y > 0:
                self.y = box.y - self.height
                self.vel_y = 0
        
        # Ekran sınırları
        if self.x < 40:
            self.x = 40
        if self.x > WIDTH - 40 - self.width:
            self.x = WIDTH - 40 - self.width
        if self.y < 0:
            self.y = 0
            self.vel_y = 0
    
    def draw(self):
        if self.is_dead:
            glColor4f(0.3, 0.3, 0.3, 0.5)
            draw_rect(self.x, self.y, self.width, self.height * 0.3, (0.3, 0.3, 0.3))
            return
        
        cx = self.x + self.width / 2
        
        if self.player_type == 'fire':
            self._draw_fireboy(cx)
        else:
            self._draw_watergirl(cx)
    
    def _draw_fireboy(self, cx):
        # Gövde
        draw_rect(self.x + 2, self.y, self.width - 4, self.height - 6, 
                  COLORS['fire_body'])
        
        # Kafa - alev şekli
        glBegin(GL_TRIANGLES)
        glColor3f(*COLORS['fire_body'])
        glVertex2f(self.x, self.y + self.height - 8)
        glVertex2f(self.x + self.width, self.y + self.height - 8)
        glColor3f(*COLORS['fire_light'])
        glVertex2f(cx, self.y + self.height + 10)
        glEnd()
        
        # İç alev
        glBegin(GL_TRIANGLES)
        glColor3f(*COLORS['fire_light'])
        glVertex2f(self.x + 5, self.y + self.height - 6)
        glVertex2f(self.x + self.width - 5, self.y + self.height - 6)
        glColor3f(1.0, 0.9, 0.3)
        glVertex2f(cx, self.y + self.height + 4)
        glEnd()
        
        # Gözler
        eye_y = self.y + self.height - 12
        glColor3f(0, 0, 0)
        glPointSize(4)
        glBegin(GL_POINTS)
        glVertex2f(self.x + 7, eye_y)
        glVertex2f(self.x + self.width - 7, eye_y)
        glEnd()
    
    def _draw_watergirl(self, cx):
        # Gövde
        draw_rect(self.x + 2, self.y, self.width - 4, self.height - 6,
                  COLORS['water_body'])
        
        # Kafa - damla şekli (yarım daire + üçgen)
        glColor3f(*COLORS['water_body'])
        glBegin(GL_POLYGON)
        for i in range(12):
            angle = math.pi * i / 11
            px = cx + 10 * math.cos(angle)
            py = self.y + self.height - 6 + 8 * math.sin(angle)
            glVertex2f(px, py)
        glEnd()
        
        # Damla ucu
        glBegin(GL_TRIANGLES)
        glColor3f(*COLORS['water_light'])
        glVertex2f(cx - 5, self.y + self.height + 2)
        glVertex2f(cx + 5, self.y + self.height + 2)
        glColor3f(*COLORS['water_body'])
        glVertex2f(cx, self.y + self.height + 10)
        glEnd()
        
        # Gözler
        eye_y = self.y + self.height - 10
        glColor3f(0, 0, 0)
        glPointSize(4)
        glBegin(GL_POINTS)
        glVertex2f(self.x + 7, eye_y)
        glVertex2f(self.x + self.width - 7, eye_y)
        glEnd()
    
    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.vel_x = 0
        self.vel_y = 0
        self.is_dead = False
        self.reached_door = False
        self.on_ground = False



# -- Elmas (Gem) --

class Gem:
    def __init__(self, x, y, gem_type):
        self.x = x
        self.y = y
        self.gem_type = gem_type  # 'fire' veya 'water'
        self.collected = False
        self.angle = 0
        self.glow = 0
    
    def update(self):
        self.angle += 3
        self.glow += 0.1
    
    def draw(self):
        if self.collected:
            return
        
        # Parıltı efekti
        glow_size = 16 + 3 * math.sin(self.glow)
        if self.gem_type == 'fire':
            glColor4f(1.0, 0.3, 0.3, 0.25)
        else:
            glColor4f(0.3, 0.6, 1.0, 0.25)
        
        glBegin(GL_POLYGON)
        for i in range(12):
            a = 2 * math.pi * i / 12
            glVertex2f(self.x + glow_size * math.cos(a),
                      self.y + glow_size * math.sin(a))
        glEnd()
        
        # Elmas şekli (dönen kare)
        if self.gem_type == 'fire':
            color = COLORS['gem_red']
            light = COLORS['gem_red_light']
        else:
            color = COLORS['gem_blue']
            light = COLORS['gem_blue_light']
        
        glBegin(GL_POLYGON)
        for i in range(4):
            a = math.radians(self.angle + i * 90 + 45)
            r = 10
            px = self.x + r * math.cos(a)
            py = self.y + r * math.sin(a)
            if i < 2:
                glColor3f(*light)
            else:
                glColor3f(*color)
            glVertex2f(px, py)
        glEnd()
        
        # Merkez parıltı
        glColor4f(1.0, 1.0, 1.0, 0.7)
        glPointSize(4)
        glBegin(GL_POINTS)
        glVertex2f(self.x, self.y)
        glEnd()
    
    def check_collect(self, player):
        if self.collected:
            return False
        
        # Sadece doğru karakter toplayabilir
        if self.gem_type != player.player_type:
            return False
        
        dist = math.sqrt((player.x + player.width/2 - self.x)**2 + 
                        (player.y + player.height/2 - self.y)**2)
        if dist < 20:
            self.collected = True
            return True
        return False



# -- Tehlike havuzlari (lav, su, zehir) --

class Hazard:
    def __init__(self, x, y, width, height, hazard_type):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.hazard_type = hazard_type  # 'lava', 'water', 'poison'
        self.wave_phase = 0
    
    def update(self):
        self.wave_phase += 0.08
    
    def draw(self):
        if self.hazard_type == 'lava':
            color1 = (0.6, 0.1, 0.0)      # En koyu
            color2 = (1.0, 0.3, 0.0)      # Orta
            color3 = (1.0, 0.6, 0.0)      # Parlak
            color4 = (1.0, 0.9, 0.3)      # En parlak
            glow = (1.0, 0.3, 0.0)
        elif self.hazard_type == 'water':
            color1 = (0.0, 0.15, 0.4)     # En koyu
            color2 = (0.0, 0.4, 0.8)      # Orta
            color3 = (0.2, 0.6, 1.0)      # Parlak
            color4 = (0.5, 0.85, 1.0)     # En parlak
            glow = (0.0, 0.4, 1.0)
        else:  # poison
            color1 = (0.0, 0.3, 0.0)      # En koyu
            color2 = (0.2, 0.7, 0.0)      # Orta
            color3 = (0.4, 0.95, 0.1)     # Parlak
            color4 = (0.7, 1.0, 0.4)      # En parlak
            glow = (0.3, 1.0, 0.0)
        
        # DIŞ PARLILTI (GLOW) - Çok belirgin
        for i in range(3):
            alpha = 0.15 - i * 0.04
            expand = (3 - i) * 4
            glColor4f(*glow, alpha)
            glBegin(GL_QUADS)
            glVertex2f(self.x - expand, self.y - expand)
            glVertex2f(self.x + self.width + expand, self.y - expand)
            glVertex2f(self.x + self.width + expand, self.y + self.height + expand)
            glVertex2f(self.x - expand, self.y + self.height + expand)
            glEnd()
        
        # ANA GÖVDE - 4 katmanlı gradient
        h = self.height / 4
        draw_rect(self.x, self.y, self.width, h, color1)
        draw_rect(self.x, self.y + h, self.width, h, color2)
        draw_rect(self.x, self.y + h * 2, self.width, h, color3)
        draw_rect(self.x, self.y + h * 3, self.width, h, color4)
        
        # ANİMASYONLU DALGA - Çok belirgin
        glColor4f(*color4, 0.9)
        glBegin(GL_TRIANGLE_STRIP)
        for i in range(int(self.width / 3) + 1):
            x_pos = self.x + i * 3
            wave = 5 * math.sin(self.wave_phase * 2 + i * 0.4)
            glVertex2f(x_pos, self.y + self.height)
            glVertex2f(x_pos, self.y + self.height + wave + 3)
        glEnd()
        
        # PARLAK KABARCIKLAR
        glColor4f(1.0, 1.0, 1.0, 0.8)
        glPointSize(5)
        glBegin(GL_POINTS)
        for i in range(4):
            bx = self.x + 8 + (i * (self.width - 16) / 3)
            by = self.y + self.height * 0.5 + 6 * math.sin(self.wave_phase * 2 + i * 1.5)
            glVertex2f(bx, by)
        glEnd()
        
        # PARLAK ÜST ÇİZGİ
        glColor3f(*color4)
        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex2f(self.x, self.y + self.height)
        glVertex2f(self.x + self.width, self.y + self.height)
        glEnd()
        
        # KOYU KENAR ÇERÇEVESİ
        glColor3f(*color1)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.width, self.y)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x, self.y + self.height)
        glEnd()
    
    def check_collision(self, player):
        # Karakterin ayak seviyesi ile tehlike üst seviyesi çakışıyor mu?
        player_bottom = player.y
        player_top = player.y + player.height
        player_left = player.x + 4
        player_right = player.x + player.width - 4
        
        hazard_top = self.y + self.height
        hazard_bottom = self.y
        hazard_left = self.x
        hazard_right = self.x + self.width
        
        # Yatay örtüşme
        horizontal_overlap = player_right > hazard_left and player_left < hazard_right
        
        # Dikey örtüşme - karakterin alt kısmı tehlikenin içinde mi?
        vertical_overlap = player_bottom < hazard_top and player_top > hazard_bottom
        
        return horizontal_overlap and vertical_overlap
    
    def is_deadly_for(self, player):
        if self.hazard_type == 'poison':
            return True
        elif self.hazard_type == 'lava' and player.player_type == 'fire':
            return False  # Ateş lavda ölmez
        elif self.hazard_type == 'water' and player.player_type == 'water':
            return False  # Su suda ölmez
        return True



# -- Kapi --

class Door:
    def __init__(self, x, y, door_type):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 55
        self.door_type = door_type
        self.glow_phase = 0
    
    def update(self):
        self.glow_phase += 0.05
    
    def draw(self, is_active):
        # Çerçeve
        glColor3f(*COLORS['door_frame'])
        glLineWidth(4)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x - 3, self.y - 2)
        glVertex2f(self.x + self.width + 3, self.y - 2)
        glVertex2f(self.x + self.width + 3, self.y + self.height + 3)
        glVertex2f(self.x - 3, self.y + self.height + 3)
        glEnd()
        
        # Kapı arka planı
        if self.door_type == 'fire':
            color = COLORS['door_fire'] if not is_active else (0.8, 0.4, 0.2)
        else:
            color = COLORS['door_water'] if not is_active else (0.2, 0.5, 0.8)
        
        draw_rect(self.x, self.y, self.width, self.height, color)
        
        # Sembol çiz
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(2)
        
        if self.door_type == 'fire':
            # Erkek sembolü ♂
            glBegin(GL_LINE_LOOP)
            for i in range(16):
                a = 2 * math.pi * i / 16
                glVertex2f(cx - 4 + 7 * math.cos(a), cy + 7 * math.sin(a))
            glEnd()
            glBegin(GL_LINES)
            glVertex2f(cx + 3, cy + 5)
            glVertex2f(cx + 12, cy + 14)
            glVertex2f(cx + 12, cy + 14)
            glVertex2f(cx + 12, cy + 8)
            glVertex2f(cx + 12, cy + 14)
            glVertex2f(cx + 6, cy + 14)
            glEnd()
        else:
            # Kadın sembolü ♀
            glBegin(GL_LINE_LOOP)
            for i in range(16):
                a = 2 * math.pi * i / 16
                glVertex2f(cx + 7 * math.cos(a), cy + 5 + 7 * math.sin(a))
            glEnd()
            glBegin(GL_LINES)
            glVertex2f(cx, cy - 2)
            glVertex2f(cx, cy - 14)
            glVertex2f(cx - 5, cy - 8)
            glVertex2f(cx + 5, cy - 8)
            glEnd()
        
        # Aktifken parıltı
        if is_active:
            glow = 0.2 + 0.15 * math.sin(self.glow_phase)
            if self.door_type == 'fire':
                glColor4f(1.0, 0.5, 0.0, glow)
            else:
                glColor4f(0.0, 0.5, 1.0, glow)
            draw_rect(self.x - 5, self.y - 3, self.width + 10, self.height + 6, 
                     (1.0, 0.5, 0.0) if self.door_type == 'fire' else (0.0, 0.5, 1.0))
    
    def check_collision(self, player):
        return check_rect_collision(player.x, player.y, player.width, player.height,
                                   self.x, self.y, self.width, self.height)



# -- Buton --

class Button:
    def __init__(self, x, y, target_elevator):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 10
        self.target = target_elevator
        self.pressed = False
    
    def check_press(self, players, box):
        # basma kontrolu
        self.pressed = False
        
        for player in players:
            if check_rect_collision(player.x, player.y - 5, player.width, 10,
                                   self.x, self.y, self.width, self.height + 5):
                self.pressed = True
                break
        
        if box and check_rect_collision(box.x, box.y - 5, box.size, 10,
                                        self.x, self.y, self.width, self.height + 5):
            self.pressed = True
        
        # Asansörü hareket ettir
        if self.target:
            self.target.activated = self.pressed
    
    def draw(self):
        h = 4 if self.pressed else self.height
        color = (0.5, 0.15, 0.5) if self.pressed else COLORS['button_purple']
        draw_rect(self.x, self.y, self.width, h, color)
        
        # Kenar
        glColor3f(0.4, 0.1, 0.4)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.width, self.y)
        glVertex2f(self.x + self.width, self.y + h)
        glVertex2f(self.x, self.y + h)
        glEnd()



# -- Kol (Lever) --

class Lever:
    def __init__(self, x, y, target_elevator):
        self.x = x
        self.y = y
        self.target = target_elevator
        self.activated = False
        self.cooldown = 0
    
    def check_interact(self, players, keys):
        # etkilesim
        if self.cooldown > 0:
            self.cooldown -= 1
            return
        
        for i, player in enumerate(players):
            dist = math.sqrt((player.x + player.width/2 - self.x)**2 +
                           (player.y + player.height/2 - self.y)**2)
            if dist < 30:
                # Etkileşim tuşu kontrolü
                interact_key = K_e if i == 1 else K_RSHIFT  # Watergirl E, Fireboy RShift
                if keys[interact_key]:
                    self.activated = not self.activated
                    self.cooldown = 20
                    if self.target:
                        self.target.activated = self.activated
                    break
    
    def draw(self):
        # Taban
        draw_rect(self.x - 8, self.y - 5, 16, 10, COLORS['lever_yellow'])
        
        # Kol
        angle = 45 if self.activated else -45
        rad = math.radians(angle)
        end_x = self.x + 18 * math.cos(rad)
        end_y = self.y + 18 * math.sin(rad)
        
        glColor3f(*COLORS['lever_yellow'])
        glLineWidth(4)
        glBegin(GL_LINES)
        glVertex2f(self.x, self.y)
        glVertex2f(end_x, end_y)
        glEnd()
        
        # Kol ucu topu
        glColor3f(0.9, 0.8, 0.2)
        glBegin(GL_POLYGON)
        for i in range(10):
            a = 2 * math.pi * i / 10
            glVertex2f(end_x + 5 * math.cos(a), end_y + 5 * math.sin(a))
        glEnd()



# -- Asansor --

class Elevator:
    def __init__(self, x, y_down, y_up, width=60, height=15):
        self.x = x
        self.y = y_down
        self.y_down = y_down
        self.y_up = y_up
        self.width = width
        self.height = height
        self.activated = False
        self.speed = 2
    
    def update(self):
        target_y = self.y_up if self.activated else self.y_down
        
        if self.y < target_y:
            self.y = min(self.y + self.speed, target_y)
        elif self.y > target_y:
            self.y = max(self.y - self.speed, target_y)
    
    def draw(self):
        # Ana platform
        draw_rect_gradient_v(self.x, self.y, self.width, self.height,
                            (0.6, 0.55, 0.65), COLORS['elevator'])
        
        # Kenar çizgisi
        glColor3f(0.5, 0.45, 0.5)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.width, self.y)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x, self.y + self.height)
        glEnd()



# -- Itilebilir Kutu --

class PushBox:
    def __init__(self, x, y, size=35):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.size = size
        self.vel_y = 0
        self.gravity = 0.4
    
    def push(self, vel_x, platforms):
        # kutuyu it
        self.x += vel_x * 0.5
        
        # Platform sınırları kontrolü
        for plat in platforms:
            if check_rect_collision(self.x, self.y, self.size, self.size,
                                   *plat.get_rect()):
                if vel_x > 0:
                    self.x = plat.x - self.size
                elif vel_x < 0:
                    self.x = plat.x + plat.width
        
        # Ekran sınırları
        if self.x < 40:
            self.x = 40
        if self.x > WIDTH - 40 - self.size:
            self.x = WIDTH - 40 - self.size
    
    def update(self, platforms, elevators):
        # Yerçekimi
        self.vel_y -= self.gravity
        self.y += self.vel_y
        
        on_ground = False
        
        # Platform çarpışması
        for plat in platforms:
            if check_rect_collision(self.x, self.y, self.size, self.size,
                                   *plat.get_rect()):
                if self.vel_y < 0:
                    self.y = plat.y + plat.height
                    self.vel_y = 0
                    on_ground = True
        
        # Asansör çarpışması
        for elev in elevators:
            if check_rect_collision(self.x, self.y, self.size, self.size,
                                   elev.x, elev.y, elev.width, elev.height):
                if self.vel_y < 0:
                    self.y = elev.y + elev.height
                    self.vel_y = 0
                    on_ground = True
        
        if self.y < 0:
            self.y = 0
            self.vel_y = 0
    
    def draw(self):
        # Gri kutu
        draw_rect_gradient_v(self.x, self.y, self.size, self.size,
                            (0.4, 0.4, 0.4), COLORS['box_gray'])
        
        # Kenar
        glColor3f(0.3, 0.3, 0.3)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.size, self.y)
        glVertex2f(self.x + self.size, self.y + self.size)
        glVertex2f(self.x, self.y + self.size)
        glEnd()
        
        # Çapraz çizgi (dekor)
        glColor3f(0.35, 0.35, 0.35)
        glBegin(GL_LINES)
        glVertex2f(self.x + 5, self.y + 5)
        glVertex2f(self.x + self.size - 5, self.y + self.size - 5)
        glVertex2f(self.x + self.size - 5, self.y + 5)
        glVertex2f(self.x + 5, self.y + self.size - 5)
        glEnd()
    
    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.vel_y = 0



# -- Bitki / dekorasyon --

class Plant:
    def __init__(self, x, y, plant_type='small'):
        self.x = x
        self.y = y
        self.plant_type = plant_type
        self.sway = x * 0.05
    
    def update(self):
        self.sway += 0.02
    
    def draw(self):
        offset = 1.5 * math.sin(self.sway)
        
        if self.plant_type == 'small':
            glColor3f(*COLORS['plant_green'])
            glLineWidth(2)
            glBegin(GL_LINES)
            glVertex2f(self.x, self.y)
            glVertex2f(self.x - 5 + offset, self.y + 10)
            glVertex2f(self.x, self.y)
            glVertex2f(self.x + offset * 0.3, self.y + 12)
            glVertex2f(self.x, self.y)
            glVertex2f(self.x + 5 + offset, self.y + 10)
            glEnd()
            
        elif self.plant_type == 'dead_tree':
            glColor3f(0.3, 0.25, 0.2)
            glLineWidth(2)
            glBegin(GL_LINES)
            glVertex2f(self.x, self.y)
            glVertex2f(self.x, self.y + 20)
            glVertex2f(self.x, self.y + 15)
            glVertex2f(self.x - 8, self.y + 22)
            glVertex2f(self.x, self.y + 15)
            glVertex2f(self.x + 8, self.y + 20)
            glVertex2f(self.x, self.y + 10)
            glVertex2f(self.x - 5, self.y + 15)
            glEnd()
            
        elif self.plant_type == 'vine':
            glColor3f(*COLORS['vine_green'])
            glLineWidth(3)
            glBegin(GL_LINE_STRIP)
            for i in range(6):
                curve = 8 * math.sin(i * 0.6 + self.sway)
                glVertex2f(self.x + curve, self.y - i * 15)
            glEnd()
            
            # Yapraklar
            glColor3f(*COLORS['plant_green'])
            for i in range(1, 5):
                ly = self.y - i * 15
                curve = 8 * math.sin(i * 0.6 + self.sway)
                side = 1 if i % 2 == 0 else -1
                
                glBegin(GL_TRIANGLES)
                glVertex2f(self.x + curve, ly)
                glVertex2f(self.x + curve + side * 10, ly + 5)
                glVertex2f(self.x + curve + side * 10, ly - 5)
                glEnd()



# -- Ana oyun sinifi --

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Ates ve Su - Tapinak Macerasi")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 28)
        
        # Ses sistemini başlat
        self._init_sounds()
        
        self._init_opengl()
        self._create_level()
        
        self.running = True
        self.level_complete = False
        self.start_time = time.time()
        self.elapsed_time = 0
        
        # Arka plan müziğini başlat
        self.music.play(-1)  # Sonsuz döngü
    
    def _init_sounds(self):
        # sesleri hazirla
        print("Sesler olusturuluyor...")
        self.gem_sound = create_gem_collect_sound()
        self.death_sound = create_death_sound()
        self.win_sound = create_win_sound()
        self.music = create_background_music()
        
        # Ses seviyelerini ayarla
        self.gem_sound.set_volume(0.6)
        self.death_sound.set_volume(0.7)
        self.win_sound.set_volume(0.8)
        self.music.set_volume(0.3)
        print("Sesler hazir!")
    
    def _init_opengl(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, WIDTH, 0, HEIGHT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
    
    def _create_level(self):
        # seviye haritasi
        
        # asansorler kaldirildi
        self.elevators = []
        
        # Zıplama parametreleri: ~80px yükseklik, ~100px yatay mesafe rahat atlanır
        
        # PLATFORMLAR - Biraz seyrekleştirildi
        self.platforms = [
            #== ZEMIN KATI (y=20)==
            Platform(40, 20, 970, 30),          # Ana zemin - tam genişlik
            
            #== 1. KAT (y=110)==
            Platform(40, 110, 140, 18),         # Sol
            Platform(280, 110, 150, 18),        # Orta-sol (tehlike gömülü)
            Platform(550, 110, 140, 18),        # Orta-sağ
            Platform(820, 110, 140, 18),        # Sağ
            
            #== 2. KAT (y=200)==
            Platform(100, 200, 160, 18),        # Sol
            Platform(380, 200, 180, 18),        # Orta (tehlike gömülü)
            Platform(700, 200, 160, 18),        # Sağ
            
            #== 3. KAT (y=290)==
            Platform(40, 290, 150, 18),         # Sol
            Platform(300, 290, 170, 18),        # Orta-sol
            Platform(600, 290, 180, 18),        # Orta-sağ (tehlike gömülü)
            Platform(880, 290, 130, 18),        # Sağ
            
            #== 4. KAT (y=380)==
            Platform(120, 380, 180, 18),        # Sol (tehlike gömülü)
            Platform(420, 380, 150, 18),        # Orta
            Platform(700, 380, 170, 18),        # Sağ
            
            #== 5. KAT (y=470)==
            Platform(40, 470, 160, 18),         # Sol
            Platform(320, 470, 180, 18),        # Orta (tehlike gömülü)
            Platform(620, 470, 150, 18),        # Orta-sağ
            # Sağ platform dikey hareketli olacak - aşağıda tanımlandı
            
            #== 6. KAT (y=560) - Köprü==
            # Sol platform hareketli olacak - aşağıda tanımlandı
            Platform(420, 560, 150, 18),        # Orta
            Platform(700, 560, 140, 18),        # Sağ
            
            #== SON KAT - KAPILAR (y=630)==
            Platform(800, 630, 210, 25),        # Kapı platformu
        ]
        
        # HAREKETLİ PLATFORMLAR
        # Yatay hareketli - 6. kat sol (kapının çapraz sol altında)
        self.moving_platform_horizontal = MovingPlatform(
            x=150, y=560, width=120, height=18,
            move_type='horizontal', min_pos=80, max_pos=280, speed=2
        )
        
        # Dikey hareketli - 5. kat sağ duvar (aşağı yukarı hareket)
        self.moving_platform_vertical = MovingPlatform(
            x=870, y=400, width=130, height=18,
            move_type='vertical', min_pos=350, max_pos=520, speed=1.5
        )
        
        # Hareketli platformlar listesi
        self.moving_platforms = [self.moving_platform_horizontal, self.moving_platform_vertical]
        
        # buton yok
        self.button = None
        
        # kol yok
        self.lever = None
        
        # kutu yok
        self.box = None
        
        # OYUNCULAR
        # Fireboy zeminde başlıyor (sol taraf) - W,A,D ile kontrol
        self.fireboy = Player(70, 55, 'fire', {
            'left': K_a,
            'right': K_d,
            'jump': K_w
        })
        
        # Watergirl zeminde başlıyor (sağ taraf) - Ok tuşları ile kontrol
        self.watergirl = Player(900, 55, 'water', {
            'left': K_LEFT,
            'right': K_RIGHT,
            'jump': K_UP
        })
        
        self.players = [self.fireboy, self.watergirl]
        
        # ELMASLAR - Sadeleştirildi, tehlike üzerinde yok
        self.gems = [
            # Zemin katı
            Gem(120, 65, 'fire'),
            Gem(600, 65, 'water'),
            Gem(900, 65, 'fire'),
            
            # 1. Kat
            Gem(100, 143, 'water'),
            Gem(600, 143, 'fire'),
            Gem(870, 143, 'water'),
            
            # 2. Kat
            Gem(160, 233, 'fire'),
            Gem(750, 233, 'water'),
            
            # 3. Kat
            Gem(100, 323, 'water'),
            Gem(370, 323, 'fire'),
            Gem(920, 323, 'water'),
            
            # 4. Kat
            Gem(480, 413, 'fire'),
            Gem(760, 413, 'water'),
            
            # 5. Kat
            Gem(100, 503, 'water'),
            Gem(670, 503, 'fire'),
            
            # 6. Kat
            Gem(480, 593, 'water'),
            Gem(750, 593, 'fire'),
        ]
        
        # TEHLİKELER - Platformların tam ortasında
        self.hazards = [
            # Zemin katı tehlikeleri
            Hazard(250, 20, 70, 40, 'lava'),
            Hazard(480, 20, 70, 40, 'water'),
            Hazard(720, 20, 70, 40, 'poison'),
            
            # 1. Kat - Platform(280, 110, 150, 18) ortası
            Hazard(330, 110, 50, 28, 'water'),
            
            # 2. Kat - Platform(380, 200, 180, 18) ortası
            Hazard(445, 200, 50, 28, 'lava'),
            
            # 3. Kat - Platform(600, 290, 180, 18) ortası
            Hazard(665, 290, 50, 28, 'poison'),
            
            # 4. Kat - Platform(120, 380, 180, 18) ortası
            Hazard(185, 380, 50, 28, 'water'),
            
            # 5. Kat - Platform(320, 470, 180, 18) ortası
            Hazard(385, 470, 50, 28, 'lava'),
        ]
        
        # KAPILAR
        self.doors = [
            Door(830, 660, 'fire'),
            Door(940, 660, 'water'),
        ]
        
        # BİTKİLER (dekorasyon) - Yeni platform konumlarına göre
        self.plants = []
        
        # Platform kenarlarına küçük bitkiler
        plant_positions = [
            # Zemin (y=50)
            (60, 55), (180, 55), (400, 55), (600, 55), (850, 55),
            # 1. Kat (y=128)
            (55, 133), (310, 133), (580, 133), (850, 133),
            # 2. Kat (y=218)
            (120, 223), (420, 223), (730, 223),
            # 3. Kat (y=308)
            (60, 313), (340, 313), (640, 313), (910, 313),
            # 4. Kat (y=398)
            (150, 403), (450, 403), (730, 403),
            # 5. Kat (y=488)
            (60, 493), (360, 493), (650, 493), (900, 493),
            # 6. Kat (y=578)
            (180, 583), (450, 583), (730, 583),
        ]
        for pos in plant_positions:
            self.plants.append(Plant(pos[0], pos[1], 'small'))
        
        # Kuru ağaçlar
        dead_trees = [
            (400, 133), (780, 223), (450, 313), (280, 403), (500, 493), (600, 583)
        ]
        for pos in dead_trees:
            self.plants.append(Plant(pos[0], pos[1], 'dead_tree'))
        
        # Sarmaşıklar (üstten sarkan)
        vines = [(150, HEIGHT - 15), (350, HEIGHT - 15), (550, HEIGHT - 15), (750, HEIGHT - 15), (950, HEIGHT - 15)]
        for pos in vines:
            self.plants.append(Plant(pos[0], pos[1], 'vine'))
    
    def _draw_background(self):
        # tugla desen arka plan
        # Ana renk
        draw_rect(40, 0, WIDTH - 80, HEIGHT, COLORS['bg_brick'])
        
        # Tuğla deseni
        glColor3f(*COLORS['bg_brick_line'])
        glLineWidth(1)
        
        brick_h = 20
        brick_w = 40
        
        for row in range(int(HEIGHT / brick_h) + 1):
            y = row * brick_h
            glBegin(GL_LINES)
            glVertex2f(40, y)
            glVertex2f(WIDTH - 40, y)
            glEnd()
            
            offset = (brick_w / 2) if row % 2 == 1 else 0
            for col in range(int((WIDTH - 80) / brick_w) + 2):
                x = 40 + col * brick_w - offset
                if 40 <= x <= WIDTH - 40:
                    glBegin(GL_LINES)
                    glVertex2f(x, y)
                    glVertex2f(x, min(y + brick_h, HEIGHT))
                    glEnd()
        
        # Yan duvarlar
        draw_rect(0, 0, 40, HEIGHT, (0.12, 0.1, 0.08))
        draw_rect(WIDTH - 40, 0, 40, HEIGHT, (0.12, 0.1, 0.08))
    
    def _draw_timer(self):
        # zamanlayici
        if not self.level_complete:
            self.elapsed_time = time.time() - self.start_time
        
        minutes = int(self.elapsed_time // 60)
        seconds = int(self.elapsed_time % 60)
        
        # Siyah altıgen arka plan
        cx, cy = WIDTH / 2, HEIGHT - 35
        glColor4f(0, 0, 0, 0.85)
        glBegin(GL_POLYGON)
        for i in range(6):
            a = math.pi / 6 + i * math.pi / 3
            glVertex2f(cx + 55 * math.cos(a), cy + 28 * math.sin(a))
        glEnd()
        
        # Kenar
        glColor3f(0.3, 0.3, 0.3)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        for i in range(6):
            a = math.pi / 6 + i * math.pi / 3
            glVertex2f(cx + 55 * math.cos(a), cy + 28 * math.sin(a))
        glEnd()
        
        # Süre metni
        time_text = f"{minutes:02d}:{seconds:02d}"
        text_surface = self.font.render(time_text, True, (255, 200, 0))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glWindowPos2f(cx - text_surface.get_width() / 2, cy - 12)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                    GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    
    def _draw_controls_hint(self):
        # kontrol bilgisi
        # Ateş - Sol tarafta (W/A/D)
        text1 = "Ates: W/A/D"
        surf1 = self.small_font.render(text1, True, (255, 150, 50))
        data1 = pygame.image.tostring(surf1, "RGBA", True)
        glWindowPos2f(50, 10)
        glDrawPixels(surf1.get_width(), surf1.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data1)
        
        # Su - Sağ tarafta (Ok tuşları)
        text2 = "Su: Ok Tuslari"
        surf2 = self.small_font.render(text2, True, (100, 180, 255))
        data2 = pygame.image.tostring(surf2, "RGBA", True)
        glWindowPos2f(WIDTH - 180, 10)
        glDrawPixels(surf2.get_width(), surf2.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data2)
    
    def _draw_gem_counter(self):
        # elmas sayaci
        fire_collected = sum(1 for g in self.gems if g.gem_type == 'fire' and g.collected)
        fire_total = sum(1 for g in self.gems if g.gem_type == 'fire')
        water_collected = sum(1 for g in self.gems if g.gem_type == 'water' and g.collected)
        water_total = sum(1 for g in self.gems if g.gem_type == 'water')
        
        # Ateş elmasları
        text1 = f"Ates: {fire_collected}/{fire_total}"
        surf1 = self.small_font.render(text1, True, (255, 100, 50))
        data1 = pygame.image.tostring(surf1, "RGBA", True)
        glWindowPos2f(50, HEIGHT - 60)
        glDrawPixels(surf1.get_width(), surf1.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data1)
        
        # Su elmasları
        text2 = f"Su: {water_collected}/{water_total}"
        surf2 = self.small_font.render(text2, True, (50, 150, 255))
        data2 = pygame.image.tostring(surf2, "RGBA", True)
        glWindowPos2f(WIDTH - 120, HEIGHT - 60)
        glDrawPixels(surf2.get_width(), surf2.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data2)
    
    def _draw_message(self, text, color):
        # mesaj kutusu
        # Arka plan
        glColor4f(0, 0, 0, 0.85)
        draw_rect(WIDTH/2 - 260, HEIGHT/2 - 45, 520, 90, (0, 0, 0))
        
        # Çerçeve
        glColor3f(*color)
        glLineWidth(3)
        glBegin(GL_LINE_LOOP)
        glVertex2f(WIDTH/2 - 260, HEIGHT/2 - 45)
        glVertex2f(WIDTH/2 + 260, HEIGHT/2 - 45)
        glVertex2f(WIDTH/2 + 260, HEIGHT/2 + 45)
        glVertex2f(WIDTH/2 - 260, HEIGHT/2 + 45)
        glEnd()
        
        # Metin
        surf = self.font.render(text, True, (255, 255, 255))
        data = pygame.image.tostring(surf, "RGBA", True)
        glWindowPos2f(WIDTH/2 - surf.get_width()/2, HEIGHT/2 - 12)
        glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)
    
    def reset_level(self):
        # level reset
        self.fireboy.reset()
        self.watergirl.reset()
        
        for gem in self.gems:
            gem.collected = False
        
        self.level_complete = False
        self.start_time = time.time()
        
        # Müziği yeniden başlat
        if not pygame.mixer.get_busy():
            self.music.play(-1)
    
    def run(self):
        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
    
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                if event.key == K_r:
                    self.reset_level()
    
    def _update(self):
        keys = pygame.key.get_pressed()
        
        # Oyuncu girdileri
        self.fireboy.handle_input(keys)
        self.watergirl.handle_input(keys)
        
        # Hareketli platformlar güncellemesi
        for mp in self.moving_platforms:
            mp.update()
        
        # Oyuncu güncellemesi
        self.fireboy.update(self.platforms, self.elevators, self.box, self.moving_platforms)
        self.watergirl.update(self.platforms, self.elevators, self.box, self.moving_platforms)
        
        # Elmas güncellemesi ve toplama (ses efekti ile)
        for gem in self.gems:
            gem.update()
            if gem.check_collect(self.fireboy):
                self.gem_sound.play()
            if gem.check_collect(self.watergirl):
                self.gem_sound.play()
        
        # Tehlike güncellemesi (ölüm sesi ile)
        for hazard in self.hazards:
            hazard.update()
            if hazard.check_collision(self.fireboy) and hazard.is_deadly_for(self.fireboy):
                if not self.fireboy.is_dead:  # Sadece ilk ölümde ses çal
                    self.death_sound.play()
                self.fireboy.is_dead = True
            if hazard.check_collision(self.watergirl) and hazard.is_deadly_for(self.watergirl):
                if not self.watergirl.is_dead:  # Sadece ilk ölümde ses çal
                    self.death_sound.play()
                self.watergirl.is_dead = True
        
        # Kapı kontrolü
        all_gems = all(g.collected for g in self.gems)
        for door in self.doors:
            door.update()
        
        if all_gems and not self.level_complete:
            fire_at_door = any(d.door_type == 'fire' and d.check_collision(self.fireboy) for d in self.doors)
            water_at_door = any(d.door_type == 'water' and d.check_collision(self.watergirl) for d in self.doors)
            
            if fire_at_door:
                self.fireboy.reached_door = True
            if water_at_door:
                self.watergirl.reached_door = True
            
            if self.fireboy.reached_door and self.watergirl.reached_door:
                self.level_complete = True
                self.win_sound.play()  # Kazanma sesi
                self.music.stop()  # Müziği durdur
        
        # Bitki animasyonu
        for plant in self.plants:
            plant.update()
    
    def _draw(self):
        glClearColor(0.1, 0.08, 0.05, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        
        # Arka plan
        self._draw_background()
        
        # Tehlikeler (platformların altında)
        for hazard in self.hazards:
            hazard.draw()
        
        # platform renkleri
        for plat in self.platforms:
            plat.draw()
        
        # Hareketli platformlar
        for mp in self.moving_platforms:
            mp.draw()
        
        # Bitkiler
        for plant in self.plants:
            plant.draw()
        
        # elmas renkleri
        for gem in self.gems:
            gem.draw()
        
        # Kapılar
        all_gems = all(g.collected for g in self.gems)
        for door in self.doors:
            door.draw(all_gems)
        
        # Oyuncular
        self.fireboy.draw()
        self.watergirl.draw()
        
        # UI
        self._draw_timer()
        self._draw_gem_counter()
        self._draw_controls_hint()
        
        # Durum mesajları
        if self.fireboy.is_dead or self.watergirl.is_dead:
            self._draw_message("OYUN BITTI! Yeniden baslatmak icin R", (1.0, 0.3, 0.3))
        elif self.level_complete:
            self._draw_message("BOLUM TAMAMLANDI! Harika!", (0.3, 1.0, 0.3))



# baslat

if __name__ == "__main__":
    game = Game()
    game.run()