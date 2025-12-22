# Subtitle Censoring Test Examples

## 🎯 New Partial Censoring Style

Your subtitles now use **partial censoring** that keeps the first and last letter visible for better readability while still being YouTube-safe!

## ✅ Censoring Examples

### Single Words:
```
Original → Subtitle
------------------------
fuck     → f**k
shit     → s**t
bitch    → b**ch
cunt     → c**t
damn     → d**n
hell     → h**l
ass      → a*s
```

### Word Variations (with suffixes):
```
Original     → Subtitle
------------------------
fucking      → f**king
fucked       → f**ked
fucker       → f**ker
shitty       → s**tty
bitches      → b**ches
motherfucker → m**ker
```

### In Sentences:
```
Input:
"Holy fuck! This cultivation technique is amazing!"

Subtitle:
"Holy f**k! This cultivation technique is amazing!"
```

```
Input:
"That fucking bastard Sasuke is so strong!" yelled Naruto.

Subtitle:
"That f**king bastard Sasuke is so strong!" yelled Naruto.
```

```
Input:
"Shit! The bitch summoned a demon!" screamed Luffy.

Subtitle:
"S**t! The b**ch summoned a demon!" screamed Luffy.
```

## 🎭 Character Names - UNCHANGED

Your character names stay exactly as written:

```
Input:
"Naruto used his fucking Rasengan!" said Sasuke.

Subtitle:
"Naruto used his f**king Rasengan!" said Sasuke.
        ↑ unchanged        ↑ unchanged      ↑ unchanged
```

More examples:
- **Naruto** → Naruto (✅)
- **Sasuke** → Sasuke (✅)
- **Uchiha** → Uchiha (✅)
- **Sharingan** → Sharingan (✅)
- **Hokage** → Hokage (✅)
- **Luffy** → Luffy (✅)
- **Goku** → Goku (✅)
- **Voldemort** → Voldemort (✅)

## 🎮 Game Terms - UNCHANGED

Technical terms stay intact:

```
Input:
"This cultivation method is fucking insane!"

Subtitle:
"This cultivation method is f**king insane!"
      ↑ unchanged
```

More examples:
- **cultivation** → cultivation (✅)
- **system** → system (✅)
- **jutsu** → jutsu (✅)
- **chakra** → chakra (✅)
- **mana** → mana (✅)
- **isekai** → isekai (✅)

## 📊 Censoring vs TTS Comparison

### For Audio (TTS):
- Uses complete replacement: "fuck" → "..." (so TTS says "period period period")
- Keeps flow natural for listening

### For Subtitles:
- Uses partial censoring: "fuck" → "f**k"
- Keeps text readable while being safe
- Viewers can still understand context

## 🧪 Test Your Setup

1. Create a test text file with:
```
"Fuck! This is amazing!" said Naruto.
"That fucking Sasuke is strong!" yelled Luffy.
"Shit! Holy shit!" screamed Goku.
```

2. Process it through your system

3. Check the `.srt` file - should show:
```
"F**k! This is amazing!" said Naruto.
"That f**king Sasuke is strong!" yelled Luffy.
"S**t! Holy s**t!" screamed Goku.
```

4. ✅ Success if:
   - Bad words are partially censored (f**k, s**t)
   - Character names are unchanged (Naruto, Sasuke, Goku)
   - Subtitles sync with audio

## 🎯 Why This Works Better

### Old Style (Complete Replacement):
```
"Holy ****! That's ****ing amazing!"
```
❌ Hard to read
❌ Context lost
❌ Looks too censored

### New Style (Partial Masking):
```
"Holy f**k! That's f**king amazing!"
```
✅ Easy to read
✅ Context clear
✅ YouTube-safe
✅ Professional appearance

## 🚀 Additional Notes

- Works with **ALL** your banned words from `config.json`
- Automatically handles **word variations** (fuck, fucking, fucked, etc.)
- **Case-insensitive** (FUCK, Fuck, fuck all become F**k)
- **Context-aware** (won't censor "Scunthorpe" or "assessment")
- **Regex-based** for accuracy

---

Happy testing! Your subtitles should now look professional and YouTube-safe! 🎉
