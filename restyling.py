import os
import sys
import random
import subprocess as sp
import concurrent.futures


# creazione del nome del file di script temporaneo
def nome_tmp_file_script(pk, file, algo=None):
    file = file[:-5]
    file += "_" + str(pk)
    if algo:
        file += "_" + algo
    return file


# generazione della lista degli input
def genera_input():
    global num_input
    # comandi sis per la sintesi
    comandi = ["source script.rugged", "eliminate x", "sweep", "fx", "resub", "simplify", "full_simplify", "collapse",
               "reduce_depth", "espresso", "decomp"]
    # sorteggio del numero previsto di comandi
    lista = []
    for _ in range(num_input):
        istruzione = comandi[random.randrange(len(comandi))]
        # calcolo del parametro da passare a eliminate
        if istruzione == "eliminate x":
            istruzione = istruzione.replace("x", str(random.randrange(-5, 6)))
        # aggiunta delle istruzioni
        lista.append(istruzione)
        lista.append("print_stats")
        # esecuzione di espresso dopo reduce_depth
        if istruzione == "reduce_depth":
            num_input -= 1
            lista.append("espresso")
            lista.append("print_stats")
    # restituzione della lista
    return lista


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
        file.write("write_blif min_" + file_tmp + ".blif\n")
        p.stdin.write("quit\n")
    # recupero output
    sis_out = str(p.communicate()[0]).split("sis> sis> ")
    sis_out.pop(0)


def tentativo_fsm(pk):
    global file_blif
    lista_istruzioni = genera_input()
    for algo in ["jedi", "nova"]:
        file_tmp = nome_tmp_file_script(pk, file_blif, algo)
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
            file.write("write_blif min_" + file_tmp + ".blif\n")
            p.stdin.write("quit\n")
        # recupero output
        sis_out = str(p.communicate()[0]).split("sis> sis> ")
        sis_out.pop(0)
        sis_out.pop(0)


# ricerca di una stt in un file e nei suoi sottocomponenti
def ricerca_kiss(file):
    with open(file, "r") as content:
        for line in content:
            if "kiss" in line:
                return True
            ''' else:
                if "search" in line and ricerca_kiss(line.split()[1]):
                    return True '''
    return False


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
    if mode != "a" and mode != "r" and mode != "ar":
        print("Inserire una modalità di minimizzazione valida")
        exit(1)
    # ricerca di una stt nel blif
    stt = ricerca_kiss(file_blif)
    # creazione ed esecuzione dei tentativi su thread diversi
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for i in range(num_tentativi):
            if not stt:
                executor.submit(tentativo_datapath, i)
            else:
                executor.submit(tentativo_fsm, i)
