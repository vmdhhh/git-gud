
import subprocess

from gitgud.skills import all_skills


def test_load(gg):
    load_tests = [
        ('git gud load 1', all_skills["1"]["1"]),
        ('git gud load rampup', all_skills["rampup"]["1"]),
        ('git gud load 3 detaching', all_skills["3"]["detaching"]),
        ('git gud load rampup 4', all_skills["rampup"]["4"]),
        ('git gud load 5-octopus', all_skills["5"]["octopus"]),
        ('git gud load rampup-4', all_skills["rampup"]["4"]),
        ('git gud load -2', all_skills["rampup"]["2"])
    ]

    for command, level in load_tests:
        subprocess.call(command, shell=True)
        assert level == gg.get_level()
