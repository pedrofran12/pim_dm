import sys
import time
import subprocess

NUMBER_OF_TESTS = 10


def main():
    for i in range(0, NUMBER_OF_TESTS):
        sys.stdout = open("./TestJoinPruneGraft" + str(i + 1) + ".txt", "w")
        p = subprocess.Popen(["python3", "ServerLog.py"], stdout=sys.stdout)
        p.wait()
        time.sleep(5)


if __name__ == '__main__':
    main()
