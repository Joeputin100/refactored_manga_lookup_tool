#!/usr/bin/env python3
"""
Complete list of best-selling manga series from Wikipedia
This contains all 100+ series from the Wikipedia page
"""

WIKIPEDIA_BEST_SELLING_MANGA_SERIES = {
    "100_million_plus": [
        "One Piece",
        "Doraemon",
        "Golgo 13",
        "Case Closed / Detective Conan",
        "Dragon Ball",
        "Naruto",
        "Demon Slayer: Kimetsu no Yaiba",
        "Slam Dunk",
        "KochiKame: Tokyo Beat Cops",
        "Crayon Shin-chan",
        "Attack on Titan",
        "Oishinbo",
        "Bleach",
        "JoJo's Bizarre Adventure",
        "Kingdom",
        "Astro Boy",
        "Baki the Grappler",
        "Fist of the North Star",
        "Hajime no Ippo",
        "Jujutsu Kaisen",
        "The Kindaichi Case Files",
        "My Hero Academia",
        "Touch"
    ],

    "50_to_99_million": [
        "Captain Tsubasa",
        "Sazae-san",
        "Kinnikuman",
        "Hunter × Hunter",
        "Vagabond",
        "Fullmetal Alchemist",
        "Sangokushi",
        "Tokyo Revengers",
        "Gintama",
        "Fairy Tail",
        "Rurouni Kenshin",
        "Berserk",
        "Haikyu!!",
        "Major",
        "Boys Over Flowers",
        "The Prince of Tennis",
        "Rokudenashi Blues",
        "Initial D",
        "That Time I Got Reincarnated as a Slime",
        "Bad Boys",
        "H2",
        "Ranma ½",
        "The Seven Deadly Sins",
        "Shura no Mon",
        "Minami no Teiō",
        "Super Radical Gag Family",
        "Blue Lock",
        "City Hunter",
        "Cobra",
        "Devilman",
        "Dragon Quest: The Adventure of Dai",
        "Fisherman Sanpei",
        "Glass Mask",
        "Great Teacher Onizuka",
        "Inuyasha",
        "Nana",
        "Saint Seiya",
        "Shoot!",
        "YuYu Hakusho"
    ],

    "30_to_49_million": [
        "Dokaben",
        "Black Jack",
        "Kosaku Shima",
        "Tokyo Ghoul",
        "Crows",
        "Dear Boys",
        "Sailor Moon",
        "Shizukanaru Don – Yakuza Side Story",
        "Ace of Diamond",
        "Shonan Junai Gumi",
        "The Promised Neverland",
        "Be-Bop High School",
        "Cooking Papa",
        "Crest of the Royal Family",
        "Kyō Kara Ore Wa!!",
        "The Apothecary Diaries",
        "Yu-Gi-Oh!",
        "Nodame Cantabile",
        "Shaman King",
        "Spy × Family",
        "20th Century Boys",
        "Black Butler",
        "Kimi ni Todoke",
        "The Chef",
        "Chibi Maruko-chan",
        "Itazura na Kiss",
        "One-Punch Man",
        "Salary Man Kintaro",
        "Urusei Yatsura",
        "Worst",
        "3×3 Eyes",
        "Frieren: Beyond Journey's End",
        "Kaze Densetsu: Bukkomi no Taku",
        "The Silent Service",
        "Yowamushi Pedal",
        "A Certain Magical Index",
        "Chainsaw Man",
        "Kuroko's Basketball",
        "Space Brothers",
        "Bastard!!",
        "Chameleon",
        "Death Note",
        "Dr. Slump",
        "Fruits Basket",
        "Gaki Deka",
        "Golden Kamuy",
        "Jarinko Chie",
        "Jingi",
        "Kaiji",
        "Pokémon Adventures",
        "Reborn!",
        "Tokimeki Tonight",
        "Toriko",
        "Ushio and Tora",
        "Yawara!"
    ],

    "20_to_29_million": [
        "Futari Ecchi",
        "Chihayafuru",
        "Hell Teacher: Jigoku Sensei Nube",
        "Shonan Bakusozoku",
        "Asari-chan",
        "The Fable",
        "Assassination Classroom",
        "D.Gray-man",
        "Eyeshield 21",
        "Sakigake!! Otokojuku",
        "Seito Shokun!",
        "Yūkan Club",
        "Bari Bari Densetsu",
        "Tsuribaka Nisshi",
        "Angel Heart",
        "Ashita no Joe",
        "Blue Exorcist",
        "Boys Be...",
        "Emblem Take 2",
        "Flame of Recca",
        "Fushigi Yûgi",
        "Hikaru no Go",
        "Magi: The Labyrinth of Magic",
        "Maison Ikkoku",
        "Miyuki",
        "Neon Genesis Evangelion",
        "Oh My Goddess!",
        "Patalliro!",
        "Parasyte",
        "The Ping Pong Club",
        "Saiyuki",
        "Ahiru no Sora",
        "Aoashi",
        "Black Clover",
        "Gantz",
        "Kaguya-sama: Love Is War",
        "Zatch Bell!",
        "Rave Master",
        "Giant Killing",
        "Himitsu Series",
        "The Rose of Versailles",
        "Ushijima the Loan Shark",
        "Abu-san",
        "Cardcaptor Sakura",
        "Hayate the Combat Butler",
        "Hoshin Engi",
        "Made in Abyss",
        "Terra Formars",
        "Dōbutsu no Oisha-san",
        "Osu! Karate Club",
        "Rookies",
        "Tsubasa: Reservoir Chronicle",
        "Dragon Quest: The Mark of Erdick",
        "Soul Eater",
        "Shōnen Shōjo Nippon no Rekishi",
        "750 Rider",
        "Buddha",
        "Cat's Eye",
        "Cuffs - Kizu Darake no Chizu",
        "Don't Call It Mystery",
        "Fire Force",
        "Food Wars!: Shokugeki no Soma",
        "Go! Go! Loser Ranger!",
        "Haruhi Suzumiya",
        "Keiji",
        "Kimagure Orange Road",
        "Love Hina",
        "Master Keaton",
        "Mazinger Z",
        "Monster",
        "Negima! Magister Negi Magi",
        "Oshi no Ko",
        "Peacock King",
        "The Quintessential Quintuplets",
        "Red River",
        "Shōnen Ashibe",
        "Sukeban Deka",
        "Swan",
        "Tasogare Ryūseigun",
        "Tokyo Daigaku Monogatari",
        "Weed"
    ]
}

def get_all_series():
    """Get all series as a flat list"""
    all_series = []
    for tier in WIKIPEDIA_BEST_SELLING_MANGA_SERIES.values():
        all_series.extend(tier)
    return all_series

def get_series_count():
    """Get total number of series"""
    return sum(len(tier) for tier in WIKIPEDIA_BEST_SELLING_MANGA_SERIES.values())

def get_series_by_tier(tier_name):
    """Get series for a specific sales tier"""
    return WIKIPEDIA_BEST_SELLING_MANGA_SERIES.get(tier_name, [])

if __name__ == "__main__":
    all_series = get_all_series()
    total_count = get_series_count()

    print(f"📚 Complete Wikipedia Best-Selling Manga List")
    print(f"=" * 60)
    print(f"Total Series: {total_count}")
    print()

    for tier_name, series_list in WIKIPEDIA_BEST_SELLING_MANGA_SERIES.items():
        print(f"{tier_name.replace('_', ' ').title()} ({len(series_list)} series):")
        for series in series_list:
            print(f"  - {series}")
        print()