import os
import sys
import time
import subprocess as sp

if __name__ == "__main__":
    # input e verifica file
    file_blif = str(sys.argv[1])
    if file_blif[-4:] != "blif":
        print("Estensione file errata")
        exit(1)
    if not os.path.exists(file_blif):
        print("File non trovato")
        exit(1)
    # tentativi da eseguire
    num_tentativi = int(sys.argv[2])
    if num_tentativi < 1:
        print("Inserire almeno 1 tentativo")
        exit(1)
    # tempo di esecuzione in secondi
    tempo_esecuzione = int(sys.argv[3])
    if tempo_esecuzione < 1:
        print("Inserire un tempo di esecuzione di almeno 1 secondo")

