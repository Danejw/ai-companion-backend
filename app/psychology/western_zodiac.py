from agents import function_tool



#@function_tool
def get_western_zodiac(month: int, day: int) -> str:
    zodiac = [
        ((1, 20), (2, 18), 'Aquarius'),
        ((2, 19), (3, 20), 'Pisces'),
        ((3, 21), (4, 19), 'Aries'),
        ((4, 20), (5, 20), 'Taurus'),
        ((5, 21), (6, 20), 'Gemini'),
        ((6, 21), (7, 22), 'Cancer'),
        ((7, 23), (8, 22), 'Leo'),
        ((8, 23), (9, 22), 'Virgo'),
        ((9, 23), (10, 22), 'Libra'),
        ((10, 23), (11, 21), 'Scorpio'),
        ((11, 22), (12, 21), 'Sagittarius'),
        ((12, 22), (12, 31), 'Capricorn'),
        ((1, 1), (1, 19), 'Capricorn')
    ]
    
    for (start_m, start_d), (end_m, end_d), sign in zodiac:
        if (month, day) >= (start_m, start_d) and (month, day) <= (end_m, end_d):
            return sign
    return 'Unknown'

def main():
    date_str = input("Enter birth date (MM/DD format, e.g. 04/15): ")
    month, day = map(int, date_str.split('/'))
    print(f"Western Zodiac: {get_western_zodiac(month, day)}")

if __name__ == "__main__":
    main() 