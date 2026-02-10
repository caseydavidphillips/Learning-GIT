print("I have information for the following planets:\n")

print("   1. Venus   2. Mars    3. Jupiter")
print("   4. Saturn  5. Uranus  6. Neptune\n")
 
while True:
    weight = input("What do you weigh on Earth?")
    try:
        value = float(weight)
        break
    except ValueError:
        print("Please enter a valid number for weight.")

while True:
    planet = int(input("Which planet do you want to visit?"))
    try:
        if 1 <= planet <= 6:
            break
    except:
            print("Please enter a number between 1 and 6.")

if planet == 1:
    print("Your weight on Venus would be", value * 0.91, "pounds.")
elif planet == 2:
    print("Your weight on Mars would be", value * 0.38, "pounds.")
elif planet == 3:
    print("Your weight on Jupiter would be", value * 2.34, "pounds.")
elif planet == 4:
    print("Your weight on Saturn would be", value * 1.06, "pounds.")
elif planet == 5:
    print("Your weight on Uranus would be", value * 0.92, "pounds.")
elif planet == 6:
    print("Your weight on Neptune would be", value * 1.19, "pounds.")