import os
import sys
import random
import subprocess as sp
import multiprocessing as mp
import concurrent.futures as cf


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
    return lista


# ricerca del minimo di nodi o di letterali e della linea a cui si giunge a quel risultato in un tentativo
def find_min(pos, lines):
    global stg, mode, lista_risultati
    # riempimento array dei nodi e dei letterali
    nodes = []
    lits = []
    for li in lines:
        nodes.append(int(li[li.find("nodes")+6:li.find("latches")]))
        if not stg:
            lits.append(int(li[li.find("lits") + 10:]))
        else:
            lits.append(int(li[li.find("lits") + 10:li.find("#states")]))
    # ricerca del minimo sull'array interessato
    ar = lits if (mode == "a") else nodes
    minimum = ar[0]
    minimum_line = 0
    for j in range(1, len(ar)):
        if ar[j] < minimum:
            minimum = ar[j]
            minimum_line = j
    # scrittura del minimo del tentativo nell'array globale
    lista_risultati[pos] = minimum, minimum_line


# esecuzione di si come sottoprocesso
def process(file, comandi, algo=None, write=True):
    global file_blif
    # file con warning ed errori di sis
    error_file = open("sis_we.txt", "a")
    # inizio processo
    p = sp.Popen(["sis"], stdin=sp.PIPE, stdout=sp.PIPE, stderr=error_file, text=True)
    # cancellazione dei primi elementi della lista altrimenti si ripetono da esecuzione con jedi
    if algo == "nova":
        for _ in range(4):
            comandi.pop(0)
    # inserimento dei comandi per stg
    if algo is not None:
        comandi.insert(0, "stg_to_network")
        comandi.insert(0, f"state_assign {algo}")
        comandi.insert(0, "state_minimize stamina")
    # inserimento del comando per lettura blif
    comandi.insert(0, f"read_blif {file_blif}")
    # apertura file in append altrimenti si cancella quando resta l'ultimo
    with open(file, "a") as f:
        # esecuzione dei comandi
        for istruzione in comandi:
            # scrittura su file solo se il comando non è print_stats e la scrittura è abilitata
            if write and istruzione != "print_stats":
                f.write(istruzione + "\n")
            p.stdin.write(istruzione + "\n")
        p.stdin.write("quit\n")
    # restituzione degli output del processo
    return str(p.communicate()[0]).split("sis> sis> ")


# esecuzione di un tentativo su datapath
def tentativo_datapath(pk):
    global file_blif
    file_tmp = nome_tmp_file_script(pk, file_blif)
    # esecuzione di sis
    sis_out = process(file_tmp, genera_input())
    sis_out.pop(0)
    find_min(pk, sis_out)


# esecuzione dello stesso tentativo su fsm sia con nova che con jedi
def tentativo_fsm(pk):
    global file_blif
    lista_istruzioni = genera_input()
    for algo in ["jedi", "nova"]:
        if algo == "jedi":
            index = pk * 2
        else:
            index = pk * 2 + 1
        file_tmp = nome_tmp_file_script(index, file_blif)
        # esecuzione di sis
        sis_out = process(file_tmp, lista_istruzioni, algo)
        sis_out.pop(0)
        sis_out.pop(0)
        find_min(index, sis_out)


# ricerca dell'indice del tentativo col risultato migliore
def best_script(lista):
    index = 0
    minimum = lista[0][0]
    for j in range(1, len(lista)):
        if lista[j][0] < minimum:
            index = j
            minimum = lista[j][0]
    return index


# creazione dello script col risultato migliore
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


# creazione del file e dello script minimi
def minimize(file):
    global stg
    # recupero statistiche
    lista_istruzioni = []
    with open(file, "r") as f:
        for line in f:
            lista_istruzioni.append(line.replace("\n", ""))
    lista_istruzioni.pop(0)
    lista_istruzioni.append("write_blif _")
    lista_istruzioni.append("print_stats")
    out = process(file, lista_istruzioni, write=False)
    out = out[len(out)-1]
    nodes = int(out[out.find("nodes") + 6:out.find("latches")])
    if not stg:
        lits = int(out[out.find("lits") + 10:])
    else:
        lits = int(out[out.find("lits") + 10:out.find("#states")])
    # completo lo script con il write_blif
    nome = file + "_" + str(nodes) + "_" + str(lits)
    with open(file, "a") as f:
        f.write("write_blif " + nome + ".blif\n")
    # cerco se esiste già un file con le stesse caratteristiche
    blif_name = nome + ".blif"
    script_name = nome + ".script"
    if os.path.exists(script_name):
        a = os.path.getsize(script_name)
        b = os.path.getsize(file)
        # se esiste e ha dimensione più grande di quello trovato, lo cancello
        if b < a:
            os.remove(blif_name)
            os.remove(script_name)
    # se il file non esiste, rinomino il blif e lo script
    if not os.path.exists(script_name):
        os.rename("_", blif_name)
        os.rename(file, script_name)
    # restituzione dei nomi dei file
    return [blif_name, script_name]


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
        print("Inserire 'a' se si vuole minimizzare per area, 'r' per ritardo")
        exit(1)
    # controllo se il file descrive una fsm
    stg = ricerca_kiss(file_blif)
    # generazione lista per il salvataggio dei risultati
    lista_risultati = [0] * num_tentativi if (not stg) else [0] * num_tentativi * 2
    # creazione ed esecuzione dei tentativi su thread diversi
    with cf.ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
        for i in range(num_tentativi):
            if not stg:
                executor.submit(tentativo_datapath, i)
            else:
                executor.submit(tentativo_fsm, i)
    # calcolo dello script migliore
    best_result = best_script(lista_risultati)
    # creazione del nuovo file di script
    file_script = crea_script(best_result, lista_risultati[best_result][1])
    # conclusione file script e generazione file minimi
    nome_min = minimize(file_script)
    # stampa finale
    print("Creato file " + nome_min[0])
    print("Creato file " + nome_min[1])
