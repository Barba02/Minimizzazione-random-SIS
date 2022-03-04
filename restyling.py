import os
import sys
import random
import multiprocessing
import subprocess as sp
import concurrent.futures


# ricerca di un stg nel file
def ricerca_kiss(file):
    with open(file, "r") as content:
        for line in content:
            if "kiss" in line:
                return True
    return False


# creazione del nome del file di script temporaneo
def nome_tmp_file_script(pk, file):
    file = file[:-5]
    file += "_" + str(pk) + ".script"
    return file


# generazione della lista degli input
def genera_input():
    global num_input
    ni = num_input
    # comandi sis per la sintesi
    comandi = ["source script.rugged", "eliminate x", "sweep", "fx", "resub", "simplify", "full_simplify", "collapse",
               "reduce_depth", "espresso", "decomp"]
    # sorteggio del numero previsto di comandi
    lista = []
    while ni > 0:
        istruzione = comandi[random.randrange(len(comandi))]
        # calcolo del parametro da passare a eliminate
        if istruzione == "eliminate x":
            istruzione = istruzione.replace("x", str(random.randrange(-5, 6)))
        # aggiunta delle istruzioni
        ni -= 1
        lista.append(istruzione)
        lista.append("print_stats")
        # esecuzione di espresso dopo reduce_depth
        if istruzione == "reduce_depth" and ni > 0:
            ni -= 1
            lista.append("espresso")
            lista.append("print_stats")
    # restituzione della lista
    return lista


# ricerca del minimo di nodi o di letterali e della linea a cui si giunge a quel risultato
def find_min(pos, lines):
    global stg, mode, lista_risultati
    nodes = []
    lits = []
    for li in lines:
        nodes.append(int(li[li.find("nodes")+6:li.find("latches")]))
        if not stg:
            lits.append(int(li[li.find("lits") + 10:]))
        else:
            lits.append(int(li[li.find("lits") + 10:li.find("#states")]))
    ar = lits if (mode == "a") else nodes
    minimum = ar[0]
    minimum_line = 0
    for j in range(1, len(ar)):
        if ar[j] < minimum:
            minimum = ar[j]
            minimum_line = j
    lista_risultati[pos] = minimum, minimum_line


# esecuzione di un tentativo su datapath
def tentativo_datapath(pk):
    global file_blif
    file_tmp = nome_tmp_file_script(pk, file_blif)
    # inizio processo
    p = sp.Popen(["sis"], stdin=sp.PIPE, stdout=sp.PIPE, text=True)  # stderr=sp.DEVNULL,
    with open(file_tmp, "w") as file:
        # intestazione del file di script
        file.write(f"read_blif {file_blif}\n")
        p.stdin.write(f"read_blif {file_blif}\n")
        # esecuzione dei comandi
        for istruzione in genera_input():
            if istruzione != "print_stats":
                file.write(istruzione + "\n")
            p.stdin.write(istruzione + "\n")
        p.stdin.write("quit\n")
    # recupero output
    sis_out = str(p.communicate()[0]).split("sis> sis> ")
    sis_out.pop(0)
    find_min(pk, sis_out)


# esecuzione dello stesso tentativo su fsm sia con nova sia con jedi
def tentativo_fsm(pk):
    global file_blif
    lista_istruzioni = genera_input()
    for algo in ["jedi", "nova"]:
        if algo == "jedi":
            index = pk * 2
        else:
            index = pk * 2 + 1
        file_tmp = nome_tmp_file_script(index, file_blif)
        # inizio processo
        p = sp.Popen(["sis"], stdin=sp.PIPE, stdout=sp.PIPE, text=True)  # stderr=sp.DEVNULL,
        with open(file_tmp, "w") as file:
            # intestazione del file di script
            file.write(f"read_blif {file_blif}\n")
            p.stdin.write(f"read_blif {file_blif}\n")
            file.write("state_minimize stamina\n")
            p.stdin.write("state_minimize stamina\n")
            file.write(f"state_assign {algo}\n")
            p.stdin.write(f"state_assign {algo}\n")
            file.write("stg_to_network\n")
            p.stdin.write("stg_to_network\n")
            # esecuzione dei comandi
            for istruzione in lista_istruzioni:
                if istruzione != "print_stats":
                    file.write(istruzione + "\n")
                p.stdin.write(istruzione + "\n")
            p.stdin.write("quit\n")
        # recupero output
        sis_out = str(p.communicate()[0]).split("sis> sis> ")
        sis_out.pop(0)
        sis_out.pop(0)
        find_min(index, sis_out)


def best_script(lista):
    index = 0
    minimum = lista[0][0]
    for j in range(1, len(lista)):
        if lista[j][0] < minimum:
            index = j
            minimum = lista[j][0]
    return index


def crea_script(index, riga):
    global file_blif, stg
    # scrittura dello script migliore
    add = 1 if (not stg) else 4
    file_tmp = nome_tmp_file_script(index, file_blif)
    file_script_name = "min_" + file_tmp[:file_tmp.rfind("_")]
    with open(file_tmp, "r") as r, open(file_script_name, "w") as w:
        for _ in range(riga+add):
            w.write(r.readline())
    # cancellazione degli altri script
    for file in os.listdir():
        if file.endswith(".script") and "min" not in file:
            os.remove(file)
    return file_script_name


# entry point
if __name__ == "__main__":
    # input e verifica file
    file_blif = str(sys.argv[1])
    if file_blif[-4:] != "blif":
        print("Estensione file errata")
        exit(1)
    if not os.path.exists(file_blif):
        print("File non trovato")
        exit(1)
    # input e verifica tentativi da eseguire
    num_tentativi = int(sys.argv[2])
    if num_tentativi < 1:
        print("Inserire almeno 1 tentativo")
        exit(1)
    # input e verifica numero di input per tentativo
    num_input = int(sys.argv[3])
    if num_input < 1:
        print("Inserire almeno 1 input per tentativo")
        exit(1)
    # input e verifica modalità di minimizzazione
    mode = str(sys.argv[4])
    if mode != "a" and mode != "r":
        print("Inserire una modalità di minimizzazione valida")
        exit(1)
    # controllo se il file è una fsm
    stg = ricerca_kiss(file_blif)
    # generazione lista per il salvataggio dei risultati
    lista_risultati = [0] * num_tentativi if (not stg) else [0] * num_tentativi * 2
    # creazione ed esecuzione dei tentativi su thread diversi
    with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        for i in range(num_tentativi):
            if not stg:
                executor.submit(tentativo_datapath, i)
            else:
                executor.submit(tentativo_fsm, i)
    # calcolo dello script migliore
    best_result = best_script(lista_risultati)
    # creazione del nuovo file di script
    file_script = crea_script(best_result, lista_risultati[best_result][1])
