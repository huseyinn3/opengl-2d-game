# 🔥💧 Ates ve Su - Tapinak Macerasi

Pygame ve OpenGL kullanarak Python ile sifirdan gelistirilen 2 kisilik platform oyunu. Klasik "Fireboy and Watergirl" oyunundan esinlenilmistir.

## 🎮 Oyun Hakkinda

Ates ve Su karakterlerini ayni anda kontrol ederek platformlar arasinda zipla, tehlikelerden kacin, elmaslari topla ve kapilara ulas. Her karakter sadece kendi turundeki elmaslari toplayabilir ve kendi elementine ait tehlikelerden etkilenmez.

## 🕹️ Kontroller

| Karakter | Hareket | Zipla |
|----------|---------|-------|
| Ates | A / D | W |
| Su | Sol / Sag Ok | Yukari Ok |

- **R** → Seviyeyi yeniden baslat
- **ESC** → Oyundan cik

## 📸 Ozellikler

- OpenGL tabanli 2D grafik render
- Iki kisilik es zamanli oynanis
- Fizik motoru (yercekimi, carpisma algilama, platform mekaniklari)
- Lav, su ve zehir havuzlari (her birinin farkli kurallari var)
- Yatay ve dikey hareketli platformlar
- Elmas toplama ve skor sistemi
- Animasyonlu tehlikeler (dalga efekti, kabarciklar)
- Bitki ve sarmasik dekorasyonlari
- Programatik ses efektleri (elmas toplama, olum, kazanma)
- Dongusel arka plan muzigi (numpy olmadan saf Python ile uretildi)
- Zamanlayici

## 🛠️ Kullanilan Teknolojiler

- **Dil:** Python
- **Grafik:** OpenGL (PyOpenGL)
- **Pencere/Girdi/Ses:** Pygame
- **Matematik:** math modulu (trigonometri, fizik hesaplari)

## 📁 Dosya Yapisi
├── ates_ve_su_opengl.py    # Ana oyun dosyasi (tek dosya)
└── README.md

## 🚀 Nasil Calistirilir

### Gereksinimler
```bash
pip install pygame PyOpenGL
```

### Calistirma
```bash
python ates_ve_su_opengl.py
```

## 🎯 Oyun Mekanikleri

- **Ates** lav havuzlarindan etkilenmez ama su ve zehir oldurur
- **Su** su havuzlarindan etkilenmez ama lav ve zehir oldurur
- **Zehir** her iki karakteri de oldurur
- Tum elmaslar toplandiktan sonra kapilar aktif olur
- Her iki karakter de kendi kapisina ulasirsa bolum tamamlanir
