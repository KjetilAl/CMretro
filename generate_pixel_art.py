from pathlib import Path
import struct

OUT = Path('assets/pixelart')
OUT.mkdir(parents=True, exist_ok=True)

COL = {
    'sky': (120, 168, 216),
    'sky_dark': (96, 136, 184),
    'grass': (64, 136, 72),
    'grass_dark': (48, 104, 56),
    'concrete': (136, 136, 144),
    'concrete_dark': (104, 104, 112),
    'white': (232, 232, 232),
    'black': (16, 16, 16),
    'blue': (72, 104, 184),
    'blue_dark': (56, 80, 152),
    'blue_light': (104, 136, 208),
    'gray': (152, 152, 160),
    'gray_dark': (112, 112, 120),
    'wood': (128, 88, 56),
    'wood_dark': (96, 64, 40),
    'chair': (84, 68, 60),
    'red': (184, 48, 48),
    'yellow': (216, 192, 56),
}


class Canvas:
    def __init__(self, w, h, bg=(0, 0, 0)):
        self.w = w
        self.h = h
        self.px = [[bg for _ in range(w)] for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def hline(self, x1, x2, y, c):
        if y < 0 or y >= self.h:
            return
        if x1 > x2:
            x1, x2 = x2, x1
        for x in range(max(0, x1), min(self.w - 1, x2) + 1):
            self.set(x, y, c)

    def rect(self, x1, y1, x2, y2, fill=None, outline=None):
        if fill is not None:
            for y in range(max(0, y1), min(self.h - 1, y2) + 1):
                for x in range(max(0, x1), min(self.w - 1, x2) + 1):
                    self.set(x, y, fill)
        if outline is not None:
            self.hline(x1, x2, y1, outline)
            self.hline(x1, x2, y2, outline)
            for y in range(y1, y2 + 1):
                self.set(x1, y, outline)
                self.set(x2, y, outline)

    def save_bmp(self, path):
        row_pad = (4 - (self.w * 3) % 4) % 4
        pixel_data_size = (self.w * 3 + row_pad) * self.h
        file_size = 54 + pixel_data_size

        with open(path, 'wb') as f:
            f.write(b'BM')
            f.write(struct.pack('<IHHI', file_size, 0, 0, 54))
            f.write(struct.pack('<IIIHHIIIIII', 40, self.w, self.h, 1, 24, 0, pixel_data_size, 2835, 2835, 0, 0))
            for y in range(self.h - 1, -1, -1):
                for x in range(self.w):
                    r, g, b = self.px[y][x]
                    f.write(bytes([b, g, r]))
                f.write(b'\x00' * row_pad)


def main_menu_stadium():
    c = Canvas(320, 200, COL['sky'])
    for y in range(0, 90, 3):
        c.hline(0, 319, y, COL['sky_dark'] if (y // 3) % 2 else COL['sky'])

    for y in range(95, 145):
        xoff = int((y - 95) * 0.4)
        c.hline(0, 319, y, COL['concrete'])
        c.hline(xoff, 319, y + 25 if y + 25 < 200 else 199, COL['concrete_dark'])

    for y in range(98, 145, 6):
        c.hline(6, 313, y, COL['gray_dark'])

    for x in (36, 284):
        c.rect(x, 54, x + 3, 95, fill=COL['gray_dark'])
        for i in range(4):
            c.rect(x - 8 + i * 4, 48, x - 5 + i * 4, 54, fill=COL['white'])

    for y in range(145, 200):
        c.hline(0, 319, y, COL['grass'])
    for y in range(150, 200, 7):
        c.hline(0, 319, y, COL['grass_dark'])
    for y in range(156, 200):
        c.set(160, y, COL['white'])

    c.save_bmp(OUT / 'main_menu_stadium.bmp')


def ui_asset_sheet():
    c = Canvas(320, 200, COL['blue'])
    c.rect(8, 8, 104, 56, fill=COL['gray'])
    c.hline(8, 104, 8, COL['white']); c.hline(8, 104, 56, COL['gray_dark'])
    for y in range(8, 57): c.set(8, y, COL['white']); c.set(104, y, COL['gray_dark'])

    c.rect(112, 8, 208, 56, fill=COL['blue_light'])
    c.hline(112, 208, 8, COL['white']); c.hline(112, 208, 56, COL['blue_dark'])
    for y in range(8, 57): c.set(112, y, COL['white']); c.set(208, y, COL['blue_dark'])

    x = 8
    for i in range(4):
        fill = COL['gray'] if i % 2 == 0 else COL['blue_light']
        dark = COL['gray_dark'] if i % 2 == 0 else COL['blue_dark']
        c.rect(x, 72, x + 72, 92, fill=fill)
        c.hline(x, x + 72, 72, COL['white']); c.hline(x, x + 72, 92, dark)
        for y in range(72, 93): c.set(x, y, COL['white']); c.set(x + 72, y, dark)
        x += 78

    c.rect(8, 104, 152, 188, fill=COL['blue'], outline=COL['white'])
    c.rect(10, 106, 150, 186, outline=COL['blue_dark'])
    c.rect(168, 104, 312, 188, fill=COL['gray'], outline=COL['white'])
    c.rect(170, 106, 310, 186, outline=COL['gray_dark'])

    # arrows
    for i in range(0, 7):
        c.hline(280 - i, 280 - i, 32, COL['white'])
        c.hline(280 + i, 280 + i, 32, COL['white'])
    c.save_bmp(OUT / 'ui_asset_sheet.bmp')


def boardroom_bg():
    c = Canvas(320, 200, (92, 96, 112))
    c.rect(0, 0, 319, 118, fill=(96, 100, 118))
    c.rect(0, 118, 319, 199, fill=(64, 64, 72))
    for x in range(0, 320, 32):
        c.rect(x, 70, x + 30, 118, fill=(86, 90, 106))
        for y in range(70, 119): c.set(x, y, (74, 78, 92))

    c.rect(124, 24, 196, 72, fill=(118, 152, 200), outline=(160, 164, 176))
    for y in range(24, 73): c.set(160, y, (160, 164, 176))
    c.hline(124, 196, 48, (160, 164, 176))

    for y in range(110, 146):
        c.hline(72 - (y - 110), 248 + (y - 110), y, COL['wood'])
    c.rect(42, 146, 278, 176, fill=COL['wood_dark'])

    for x in range(50, 271, 20):
        for y in range(148, 175):
            c.set(x, y, (84, 56, 36))

    for x in (84, 128, 172, 216):
        c.rect(x, 132, x + 20, 146, fill=COL['chair'])
        c.rect(x + 2, 122, x + 18, 132, fill=(96, 80, 72))

    c.save_bmp(OUT / 'boardroom_background.bmp')


def icons_set():
    c = Canvas(104, 24, (32, 32, 48))
    size = 16
    pad = 4
    for i in range(5):
        x = pad + i * (size + pad)
        c.rect(x, pad, x + 15, pad + 15, fill=(72, 72, 88), outline=(120, 120, 136))

    x, y = pad, pad
    c.rect(x + 6, y + 3, x + 9, y + 12, fill=COL['red'])
    c.rect(x + 3, y + 6, x + 12, y + 9, fill=COL['red'])

    x = pad + (size + pad)
    c.rect(x + 4, y + 3, x + 11, y + 12, fill=COL['yellow'], outline=(160, 136, 40))

    x = pad + 2 * (size + pad)
    c.rect(x + 4, y + 3, x + 11, y + 12, fill=COL['red'], outline=(136, 40, 40))

    x = pad + 3 * (size + pad)
    c.rect(x + 2, y + 2, x + 13, y + 13, fill=(220, 220, 220), outline=COL['black'])
    c.rect(x + 6, y + 6, x + 9, y + 9, fill=COL['black'])

    x = pad + 4 * (size + pad)
    c.hline(x + 3, x + 10, y + 8, COL['white'])
    for i in range(4):
        c.set(x + 10 + i, y + 8 - i, COL['white'])
        c.set(x + 10 + i, y + 8 + i, COL['white'])

    c.save_bmp(OUT / 'player_status_icons.bmp')


def main():
    main_menu_stadium()
    ui_asset_sheet()
    boardroom_bg()
    icons_set()
    print(f'Generated assets in {OUT}')


if __name__ == '__main__':
    main()
