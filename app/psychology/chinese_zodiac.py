

#@function_tool
def get_chinese_zodiac(year: int) -> str:
    animals = ['Rat', 'Ox', 'Tiger', 'Rabbit', 'Dragon', 'Snake', 'Horse', 'Goat', 'Monkey', 'Rooster', 'Dog', 'Pig']
    return animals[(year - 1900) % 12]

def main():
    year = int(input("Enter birth year (e.g. 1990): "))
    print(f"Chinese Zodiac: {get_chinese_zodiac(year)}")

if __name__ == "__main__":
    main() 