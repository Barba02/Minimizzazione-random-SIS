import concurrent.futures
import os
import random
import sys
import time
import subprocess as sp


def nome_tmp_file_script(pk, file, algo):
    file = file[:-5]
    file += "_" + str(pk)
    if algo:
        file += "_" + algo
    return file


# esecuzione di un tentativo di minimizzazione di fsm per n secondi
def tentativo(pk, assign_algo=None):
    global file_blif, tempo_esecuzione, stt, comandi
    file_tmp = nome_tmp_file_script(pk, file_blif, assign_algo)
    # inizio processo
    p = sp.Popen(["sis"], stdin=sp.PIPE, stdout=sp.PIPE, text=True)  # stderr=sp.DEVNULL,
    with open(file_tmp, "w") as file:
        # intestazione del file di script
        file.write(f"read_blif \"{file_blif}\"\n")
        p.stdin.write(f"read_blif \"{file_blif}\"\n")
        if stt:
            file.write("state_minimize stamina\n")
            p.stdin.write("state_minimize stamina\n")
            file.write(f"state_assign {assign_algo}\n")
            p.stdin.write(f"state_assign {assign_algo}\n")
            file.write("stg_to_network\n")
            p.stdin.write("stg_to_network\n")
        # esecuzione dei comandi
        fine = time.time() + tempo_esecuzione
        while time.time() <= fine:
            istruzione = comandi[random.randrange(len(comandi))]
            # generazione parametro di eliminate
            if istruzione == "eliminate x":
                istruzione = istruzione.replace("x", str(random.randrange(-5, 6)))
            file.write(istruzione + "\n")
            p.stdin.write(istruzione + "\n")
            p.stdin.write("print_stats\n")
            # esecuzione di espresso dopo reduce_depth
            if istruzione == "reduce_depth":
                file.write("espresso\n")
                p.stdin.write("espresso\n")
                p.stdin.write("print_stats\n")
        p.stdin.write("quit\n")
    # recupero output
    sis_out = str(p.communicate()[0]).split("sis> sis> ")
    sis_out.pop(0)
    if stt:
        sis_out.pop(0)
    print(sis_out)


# ricerca di una stt in un file e nei suoi sottocomponenti
def ricerca_kiss(file):
    with open(file, "r") as content:
        for line in content:
            if "kiss" in line:
                return True
            else:
                if "search" in line and ricerca_kiss(line.split()[1]):
                    return True
    return False


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
    # input e verifica tempo di esecuzione in secondi
    tempo_esecuzione = int(sys.argv[3])
    if tempo_esecuzione < 1:
        print("Inserire un tempo di esecuzione di almeno 1 secondo")
        exit(1)
    # input e verifica modalità di minimizzazione
    mode = str(sys.argv[4])
    if mode != "a" and mode != "r" and mode != "ar":
        print("Inserire una modalità di minimizzazione valida")
        exit(1)
    # ricerca di una stt nel blif
    stt = ricerca_kiss(file_blif)
    # lista dei comandi di sis per la sintesi
    comandi = ["source script.rugged", "eliminate x", "sweep", "fx", "resub", "simplify", "full_simplify", "collapse",
               "reduce_depth", "espresso", "decomp"]
    # creazione ed esecuzione dei tentativi su thread diversi
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(num_tentativi):
            if not stt:
                executor.submit(tentativo, i)
            else:
                executor.submit(tentativo, i, "jedi")
                executor.submit(tentativo, i, "nova")
