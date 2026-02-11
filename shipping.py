weight = 41.5

#Ground Shipping
if weight <= 2:
    cost = 1.5 * weight + 20
    print(f"It will cost ${cost:.2f} to ship this package via Ground Shipping.")
elif weight > 2 and weight <= 6:
    cost = 3 * weight + 20
    print(f"It will cost ${cost:.2f} to ship this package via Ground Shipping.")
elif weight > 6 and weight <= 10:
    cost = 4 * weight + 20
    print(f"It will cost ${cost:.2f} to ship this package via Ground Shipping.")
else:
    cost = 4.75 * weight + 20
    print(f"It will cost ${cost:.2f} to ship this package via Ground Shipping.")

#Premium Ground Shipping
cost_premium = 125.00
print(f"It will cost ${cost_premium:.2f} to ship this package via Premium Ground Shipping.")

#Drone Shipping
if weight <= 2:
    cost_drone = 4.5 * weight
    print(f"It will cost ${cost_drone:.2f} to ship this package via Drone Shipping.")
elif weight > 2 and weight <= 6:
    cost_drone = 9 * weight
    print(f"It will cost ${cost_drone:.2f} to ship this package via Drone Shipping.")
elif weight > 6 and weight <= 10:
    cost_drone = 12 * weight
    print(f"It will cost ${cost_drone:.2f} to ship this package via Drone Shipping.")
else:
    cost_drone = 14.25 * weight
    print(f"It will cost ${cost_drone:.2f} to ship this package via Drone Shipping.")