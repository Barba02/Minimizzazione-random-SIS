import os
import sys
import random
import subprocess as sp


# lettura dei parametri in input
blif = str(sys.argv[1])
stg = str(sys.argv[2])
stg = True if (("t" in stg) or ("T" in stg)) else False
min_nodes = int(sys.argv[3])
min_lits = int(sys.argv[4])
# lista dei comandi di sis per la sintesi
commands = ["source script.rugged", "eliminate x", "sweep", "fx", "resub", "simplify", "full_simplify", "collapse",
            "reduce_depth", "espresso", "decomp", "invert", "invert_io"]
# esecuzione di n prove
for _ in range(int(sys.argv[5])):
    # lettura/creazione e aggiornamento dell'indice del test
    if os.path.exists("auto_increment.txt"):
        with open("auto_increment.txt", "r") as ai:
            pk = int(ai.readline())
    else:
        pk = 0
    with open("auto_increment.txt", "w") as ai:
        ai.write(str(pk+1))
    # inizio sottoprocesso
    process = sp.Popen(["sis"], stdin=sp.PIPE, stdout=sp.PIPE, text=True)
    with open(blif[:-5] + "_" + str(pk) + "_comandi.txt", "w") as comandi:
        process.stdin.write("read_blif \"" + blif + "\"\n")
        # comandi per portare la stg in circuito
        if stg:
            assign_algo = "jedi" if (random.random() % 2 == 0) else "nova"
            comandi.write("state_assign " + assign_algo + "\n")
            process.stdin.write("state_minimize\n")
            process.stdin.write("state_assign " + assign_algo + "\n")
            process.stdin.write("stg_to_network\n")
            process.stdin.write("print_stats\n")
        # esecuzione di n comandi con relativa scrittura, n parametro da terminale
        for _ in range(int(sys.argv[6])):
            cmd = commands[random.randrange(10)]
            # parametro di eliminate
            if cmd == "eliminate x":
                cmd = cmd.replace("x", str(random.randrange(-5, 6)))
            comandi.write(cmd + "\n")
            process.stdin.write(cmd + "\n")
            process.stdin.write("print_stats\n")
            # esecuzione di espresso dopo reduce_depth
            if cmd == "reduce_depth":
                cmd = "espresso"
                comandi.write(cmd + "\n")
                process.stdin.write(cmd + "\n")
                process.stdin.write("print_stats\n")
        process.stdin.write("quit\n")
    # recupero output sottoprocesso
    lines = str(process.communicate()[0]).split("sis> sis> ")
    lines.pop(0)
    if stg:
        lines.pop(0)
    # stampa delle statistiche
    with open(blif[:-5] + "_" + str(pk) + "_stats.txt", "w") as stats:
        for line in lines:
            nodes = int(line[line.find("nodes")+6:line.find("latches")])
            if stg:
                lits = int(line[line.find("lits") + 10:line.find("#states")])
            else:
                lits = int(line[line.find("lits")+10:])
            stats.write(str(nodes) + " " + str(lits))
            # evidenziazione di statistiche valide
            if nodes <= min_nodes:
                min_nodes = nodes
                stats.write("\t\tless nodes")
            if lits <= min_lits:
                min_lits = lits
                stats.write("\t\tless lits")
            stats.write("\n")
# pulitore
toRemove = []
mode = str(sys.argv[7])
mode = mode if (("m" in mode) or ("n" in mode)) else "mn"
ai = "auto_increment.txt"
n = int(open(ai, "r").readline())
os.remove(ai)
for i in range(0, n):
    st = blif[:-5] + "_" + str(i) + "_stats.txt"
    cmd = blif[:-5] + "_" + str(i) + "_comandi.txt"
    if os.path.exists(st):
        with open(st, "r") as file:
            if mode == "m":
                if file.read().find("lits") == -1:
                    toRemove.append(st)
                    toRemove.append(cmd)
            elif mode == "n":
                if file.read().find("nodes") == -1:
                    toRemove.append(st)
                    toRemove.append(cmd)
            else:
                if file.read().find("lits") == -1 and file.read().find("nodes") == -1:
                    toRemove.append(st)
                    toRemove.append(cmd)
    else:
        if os.path.exists(cmd):
            os.remove(cmd)
for x in toRemove:
    if os.path.exists(x):
        os.remove(x)
