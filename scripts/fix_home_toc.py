from pathlib import Path

p = Path(r"c:\Users\Администратор\Documents\GитHub\onlinecasinoexperte.org\src\pages\_body.html")
t = p.read_text(encoding="utf-8")

replacements = [
    (
        'href="#1-das-beste-online-casino-im-vergleich-goodman-casino">1. Das beste Online Casino im Vergleich: Goodman Casino</a>',
        'href="#1-das-beste-online-casino-im-vergleich-skycrown-casino">1. Das beste Online Casino im Vergleich: SkyCrown Casino</a>',
    ),
    ('href="#2-casinobuck">2. Casinobuck</a>', 'href="#2-goodman-casino">2. Goodman Casino</a>'),
    ('href="#3-gioo-casino">3. Gioo Casino</a>', 'href="#3-horus-casino">3. Horus Casino</a>'),
    ('href="#4-hejgo-casino">4. HEJGO Casino</a>', 'href="#4-gioo-casino">4. Gioo Casino</a>'),
    ('href="#5-gslot">5. GSlot</a>', 'href="#5-casinobuck">5. CasinoBuck</a>'),
]

changed = 0
for old, new in replacements:
    if old in t:
        t = t.replace(old, new, 1)
        changed += 1
    else:
        print("missing:", old[:60])

p.write_text(t, encoding="utf-8")
print("changed", changed)
