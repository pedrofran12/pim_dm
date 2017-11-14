import rpyc
import time
from subprocess import Popen

def test_neighbor_table(router_id_str, router_rpc, expected_neighbors):
    print("\ttesting " + router_id_str)
    success = False
    while not success:
        (table, dict) = router_rpc.root.get_neighbors()
        if "eth0" in dict:
            neighbors_of_eth = dict["eth0"]
        elif len(expected_neighbors) != 0:
            print("\t\x1b[1;31;20m[NOT OK]\x1b[0m " + router_id_str + " table empty")
            time.sleep(5)
            continue
        else:
            print("\t\x1b[1;32;40m[OK]\x1b[0m " + router_id_str + " neighbor table is empty")
            break
        if len(expected_neighbors) != len(neighbors_of_eth):
            print("\t\x1b[1;31;20m[NOT OK]\x1b[0m " + router_id_str + " different number of neighbors")
            time.sleep(5)
            continue
        success = True
        for n in expected_neighbors:
            if (n not in neighbors_of_eth):
                print("\t\x1b[1;31;20m[NOT OK]\x1b[0m " + router_id_str + " doesn't know about " + n)
                print("\t ... trying again ...")
                success = False
                time.sleep(2)
                break
    print("\t\x1b[1;32;20m[OK]\x1b[0m " + router_id_str + " success")
    print(table + "\n\n\n")
    return dict


print("START TCPDUMP CAPTURE")
p = Popen(['tcpdump', '-i', 'br0', '-w', './capture.pcap'])
ips = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4"]
expected_neighbors = [["10.0.0.2", "10.0.0.3", "10.0.0.4"], ["10.0.0.1", "10.0.0.3", "10.0.0.4"], ["10.0.0.1", "10.0.0.2", "10.0.0.4"], ["10.0.0.2", "10.0.0.3", "10.0.0.1"]]
r1 = rpyc.connect("10.0.0.1", 10000)
r2 = rpyc.connect("10.0.0.2", 10000)
r3 = rpyc.connect("10.0.0.3", 10000)
r4 = rpyc.connect("10.0.0.4", 10000)
print("Test1: Start PIM process and check if neighbor tables are empty")
test_neighbor_table("R1", r1, [])
test_neighbor_table("R2", r2, [])
test_neighbor_table("R3", r3, [])
test_neighbor_table("R4", r4, [])
print("\x1b[1;32;20m[OK]\x1b[0m Test1 success")
print("============================\n\n\n")


print("Enabling R1's interface eth0...")
r1.root.add_interface("eth0")
print("Enabling R2's interface eth0...")
r2.root.add_interface("eth0")
print("Enabling R3's interface eth0...")
r3.root.add_interface("eth0")
print("Enabling R4's interface eth0...")
r4.root.add_interface("eth0")


print("Test2: Check if routers establish neighborship relations")
dict = test_neighbor_table("R1", r1, expected_neighbors[0])
test_neighbor_table("R2", r2, expected_neighbors[1])
test_neighbor_table("R3", r3, expected_neighbors[2])
test_neighbor_table("R4", r4, expected_neighbors[3])
print("\x1b[1;32;20m[OK]\x1b[0m Test2 Success")
print("============================\n\n\n")
print("Test3: Disable Router3 and check if others router react to R3 HelloHoldTime=0")
print("Disabling R3's interface eth0...")
r3.root.remove_interface("eth0")


expected_neighbors = [["10.0.0.2", "10.0.0.4"], ["10.0.0.1", "10.0.0.4"], [], ["10.0.0.2", "10.0.0.1"]]
test_neighbor_table("R1", r1, expected_neighbors[0])
test_neighbor_table("R2", r2, expected_neighbors[1])
test_neighbor_table("R4", r4, expected_neighbors[3])
print("\x1b[1;32;20m[OK]\x1b[0m Test3 success")

print("============================\n\n\n")
print("Test4: KILL router (doesn't send Hello with HelloHoldTime set to 0) and check if others remove that router after timeout")

print("Route4 has HelloHoldTime set to: " + str(dict["eth0"]["10.0.0.4"][0]))
print("Killing router4...")
r4.root.kill()
print("Waiting for " + str(str(dict["eth0"]["10.0.0.4"][0])) + " seconds...")
time.sleep(int(dict["eth0"]["10.0.0.4"][0]))



expected_neighbors = [["10.0.0.2"], ["10.0.0.1"], [], []]

test_neighbor_table("R1", r1, expected_neighbors[0])
test_neighbor_table("R2", r2, expected_neighbors[1])
print("\x1b[1;32;20m[OK]\x1b[0m Test4 success")


print("============================\n\n\n")
print("Test5: ReEnable router R3 and check if Generation ID is different")

print("R3 had old GenerationID set to: " + str(dict["eth0"]["10.0.0.3"][1]))
print("Enabling router3...")
r3.root.add_interface("eth0")
print("Enabled router3...")
expected_neighbors = [["10.0.0.2", "10.0.0.3"], ["10.0.0.1", "10.0.0.3"], ["10.0.0.1", "10.0.0.2"], []]
new_dict_r1 = test_neighbor_table("R1", r1, expected_neighbors[0])
new_dict_r2 = test_neighbor_table("R2", r2, expected_neighbors[1])
new_dict_r3 = test_neighbor_table("R3", r3, expected_neighbors[2])

print("R1 has in its neighbor table, R3 with GenerationID set to: " + new_dict_r1["eth0"]["10.0.0.3"][1])
print("R2 has in its neighbor table, R3 with GenerationID set to: " + new_dict_r2["eth0"]["10.0.0.3"][1])
if new_dict_r1["eth0"]["10.0.0.3"][1] == new_dict_r2["eth0"]["10.0.0.3"][1]:
    print("\x1b[1;32;20m[OK]\x1b[0m R1 and R2 have same R3's GenerationID")
else:
    print("\x1b[1;31;20m[NOT OK]\x1b[0m R1 and R2 have different R3's GenerationID")
    exit()

if dict["eth0"]["10.0.0.3"][1] != new_dict_r2["eth0"]["10.0.0.3"][1]:
    print("\x1b[1;32;20m[OK]\x1b[0m old and new GenerationID are differents (" + dict["eth0"]["10.0.0.3"][1] + " != " + new_dict_r1["eth0"]["10.0.0.3"][1] + ")")
else:
    print("\x1b[1;31;20m[NOT OK]\x1b[0m old and new GenerationID are equal (" + dict["eth0"]["10.0.0.3"][1] + " == " + new_dict_r1["eth0"]["10.0.0.3"][1] + ")")
    exit()

print("FINISH TCPDUMP CAPTURE")
p.terminate()