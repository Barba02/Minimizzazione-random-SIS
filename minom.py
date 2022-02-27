import os
import sys
import random
import subprocess as sp


# rimozione dei file che non producono risultati
def clear():
    global blif, mode
    to_remove = []
    # lettura del numero di file da considerare e rimozione del file con la pk
    ai_ = "auto_increment.txt"
    n = int(open(ai_, "r").readline())
    os.remove(ai_)
    # scorrimento di tutti i file di statistiche e comandi
    for i in range(0, n):
        st = blif[:-5] + "_" + str(i) + "_stats.txt"
        cmd_ = blif[:-5] + "_" + str(i) + "_comandi.txt"
        # se le statistiche non sono da considerare, aggiungo i due file alla lista di quelli da rimuovere
        if os.path.exists(st):
            with open(st, "r") as file:
                if mode == "m":
                    if file.read().find("lits") == -1:
                        to_remove.append(st)
                        to_remove.append(cmd_)
                elif mode == "n":
                    if file.read().find("nodes") == -1:
                        to_remove.append(st)
                        to_remove.append(cmd_)
                else:
                    if file.read().find("lits") == -1 and file.read().find("nodes") == -1:
                        to_remove.append(st)
                        to_remove.append(cmd_)
        # se non esiste il file di statistiche, ma esiste il file dei comandi, elimino solo quello
        else:
            if os.path.exists(cmd_):
                to_remove.append(cmd_)
    # rimozione di tutti i file in lista
    for x in to_remove:
        if os.path.exists(x):
            os.remove(x)


# conversione dei file di comandi in script sis
def script_generation():
    global blif, stg, mode, min_lits, min_nodes
    txt = []
    # lista dei file di statistiche
    for file in os.listdir():
        if file[-9:] == "stats.txt":
            txt.append(file)
    # lettura dei file
    for file in txt:
        counter = 1
        ml = min_lits
        mn = min_nodes
        # ricerca dell'ultima riga da tenere in base alla modalità
        with open(file, "r") as st:
            for file_row in st:
                str_ = file_row.split()
                if mode == "m":
                    if ("lits" in file_row) and str_[0] != mn and str_[1] != ml:
                        mn = str_[0]
                        ml = str_[1]
                        row = counter
                elif mode == "n":
                    if "nodes" in file_row:
                        mn = str_[0]
                        ml = str_[1]
                        row = counter
                else:
                    if ("lits" in file_row) or ("nodes" in file_row):
                        mn = str_[0]
                        ml = str_[1]
                        row = counter
                counter += 1
        # lettura del corrispondente file di comandi fino alla riga trovata
        script = "read_blif " + blif + "\n"
        nome_file = blif[:-5] + "_" + mn + "_" + ml
        with open(file.replace("stats", "comandi"), "r") as cm:
            counter = 1
            for file_row in cm:
                if counter <= row:
                    script += file_row
                else:
                    break
                counter += 1
            script += "write_blif " + nome_file + ".blif" + "\n"
        # creazione del file di script
        with open(nome_file + ".script", "w") as cm:
            cm.write(script)
    # rimozione dei file di statistiche e comandi
    for file in txt:
        os.remove(file)
        os.remove(file.replace("stats", "comandi"))


def min_blif():
    # lista degli script
    script = []
    for file in os.listdir():
        if file[-6:] == "script":
            script.append(file)
    # esecuzione degli script
    for file in script:
        pr = sp.Popen(["sis"], stdin=sp.PIPE, stdout=sp.PIPE, text=True)
        for file_row in file:
            pr.stdin.write(file_row + "\n")



if __name__ == "__main__":
    # lettura dei parametri in input e verifica di questi
    blif = str(sys.argv[1])
    stg = str(sys.argv[2])
    stg = True if (("t" in stg) or ("T" in stg)) else False
    min_nodes = int(sys.argv[3])
    min_nodes = min_nodes if (min_nodes > 0) else 9999
    min_lits = int(sys.argv[4])
    min_lits = min_lits if (min_lits > 0) else 9999
    prove = int(sys.argv[5])
    prove = prove if (prove > 0) else 8
    comandi_per_prova = int(sys.argv[6])
    comandi_per_prova = comandi_per_prova if (comandi_per_prova > 0) else 16
    mode = str(sys.argv[7])
    mode = mode if (("m" in mode) or ("n" in mode)) else "mn"
    # lista dei comandi di sis per la sintesi
    commands = ["source script.rugged", "eliminate x", "sweep", "fx", "resub", "simplify", "full_simplify", "collapse",
                "reduce_depth", "espresso", "decomp", "invert", "invert_io"]
    # esecuzione di n prove
    for _ in range(prove):
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
            for _ in range(comandi_per_prova):
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
    clear()
    # generazione dello script
    script_generation()
    # creazione dei blif minimizzati con gli script
    min_blif()
