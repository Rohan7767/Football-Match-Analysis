broadcast_name_map = {
    2: "Valverde",
    16: "Carvajal",
    70: "Carvajal",
    14: "Benzema",
    12: "Vinicius Jr",
    106: "Vinicius Jr",
    11: "Kroos",
    13: "Van Dijk",
    20: "Fabinho",
    21: "Henderson",
    15: "Konate",
    18: "Trent",
    25: "Allison",
    104: "Allison",
    139: "Fabinho",
    58: "Valverde",
}
tracker_red_team = {
    1: "Trent", 9: "Konate", 17: "Van Dijk", 3: "Salah",
    12: "Henderson", 16: "Fabinho", 6: "Mane", 42: "Allison",
    67: "Allison", 21: "Luis Diaz", 86: "Luis Diaz", 15: "Robertson",
    59: "Robertson", 4: "Thiago"
}
tracker_white_team = {
    10: "Vinicius Jr", 11: "Benzema", 19: "Valverde", 8: "Mendy",
    5: "Kroos", 18: "Modric", 20: "Carvajal", 61: "Carvajal",
    7: "Rudiger", 2: "Militao", 14: "Casemiro"
}
tracker_name_map = {**tracker_red_team, **tracker_white_team}
common_ids = set(broadcast_name_map.keys()) & set(tracker_name_map.keys())
print("Common track IDs and corresponding names:")
for tid in sorted(common_ids):
    b_name = broadcast_name_map[tid]
    t_name = tracker_name_map[tid]
    print(f"Track ID {tid}: BroadcastTracker -> {b_name}, Tracker -> {t_name}")
unique_to_broadcast = set(broadcast_name_map.keys()) - set(tracker_name_map.keys())
unique_to_tracker = set(tracker_name_map.keys()) - set(broadcast_name_map.keys())
print("\nIDs only in broadcast_tracker.py:", unique_to_broadcast)
print("IDs only in tracker.py:", unique_to_tracker)
