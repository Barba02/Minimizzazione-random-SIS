import os
import sys
import random
import subprocess as sp
import concurrent.futures


def nome_tmp_file_script(pk, file, algo=None):
    file = file[:-5]
    file += "_" + str(pk)
    if algo:
        file += "_" + algo
    return file


def tentativo_datapath(pk):
    global file_blif, num_input, comandi
    file_tmp = nome_tmp_file_script(pk, file_blif)
    # inizio processo
    p = sp.Popen(["sis"], stdin=sp.PIPE, stdout=sp.PIPE, text=True)  # stderr=sp.DEVNULL,
    with open(file_tmp, "w") as file:
        # intestazione del file di script
        file.write(f"read_blif \"{file_blif}\"\n")
        p.stdin.write(f"read_blif \"{file_blif}\"\n")
        # esecuzione dei comandi
        for _ in range(num_input):
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
        file.write("write_blif min_" + file_tmp + ".blif")
        p.stdin.write("quit\n")
    # recupero output
    sis_out = str(p.communicate()[0]).split("sis> sis> ")
    sis_out.pop(0)
    print(sis_out)


def tentativo_fsm(pk):
    global file_blif, num_input, comandi
    file_1 = nome_tmp_file_script(pk, file_blif, "jedi")
    file_2 = nome_tmp_file_script(pk, file_blif, "nova")
    # inizio processo
    p1 = sp.Popen(["sis"], stdin=sp.PIPE, stdout=sp.PIPE, text=True)
    p2 = sp.Popen(["sis"], stdin=sp.PIPE, stdout=sp.PIPE, text=True)
    with open(file_1, "w") as f1, open(file_2, "w") as f2:
        # intestazione dei file di script
        f1.write(f"read_blif \"{file_blif}\"\n")
        f2.write(f"read_blif \"{file_blif}\"\n")
        p1.stdin.write(f"read_blif \"{file_blif}\"\n")
        p2.stdin.write(f"read_blif \"{file_blif}\"\n")
        f1.write("state_minimize stamina\n")
        f2.write("state_minimize stamina\n")
        p1.stdin.write("state_minimize stamina\n")
        p2.stdin.write("state_minimize stamina\n")
        f1.write("state_assign jedi\n")
        f2.write("state_assign nova\n")
        p1.stdin.write("state_assign jedi\n")
        p2.stdin.write("state_assign nova\n")
        f1.write("stg_to_network\n")
        f2.write("stg_to_network\n")
        p1.stdin.write("stg_to_network\n")
        p2.stdin.write("stg_to_network\n")
        # esecuzione dei comandi
        for _ in range(num_tentativi):
            istruzione = comandi[random.randrange(len(comandi))]
            # generazione parametro di eliminate
            if istruzione == "eliminate x":
                istruzione = istruzione.replace("x", str(random.randrange(-5, 6)))
            f1.write(istruzione + "\n")
            f2.write(istruzione + "\n")
            p1.stdin.write(istruzione + "\n")
            p2.stdin.write(istruzione + "\n")
            p1.stdin.write("print_stats\n")
            p2.stdin.write("print_stats\n")
            # esecuzione di espresso dopo reduce_depth
            if istruzione == "reduce_depth":
                f1.write("espresso\n")
                f2.write("espresso\n")
                p1.stdin.write("espresso\n")
                p2.stdin.write("espresso\n")
                p1.stdin.write("print_stats\n")
                p2.stdin.write("print_stats\n")
        f1.write("write_blif min_" + file_1 + ".blif")
        f2.write("write_blif min_" + file_2 + ".blif")
        p1.stdin.write("quit\n")
        p2.stdin.write("quit\n")
    # recupero output
    sis_out1 = str(p1.communicate()[0]).split("sis> sis> ")
    sis_out1.pop(0)
    sis_out1.pop(0)
    sis_out2 = str(p2.communicate()[0]).split("sis> sis> ")
    sis_out2.pop(0)
    sis_out2.pop(0)
    print(sis_out1, sis_out2)


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
    # lista dei comandi di sis per la sintesi
    comandi = ["source script.rugged", "eliminate x", "sweep", "fx", "resub", "simplify", "full_simplify", "collapse",
               "reduce_depth", "espresso", "decomp"]
    # creazione ed esecuzione dei tentativi su thread diversi
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for i in range(num_tentativi):
            if not stt:
                executor.submit(tentativo_datapath, i)
            else:
                executor.submit(tentativo_fsm, i)
