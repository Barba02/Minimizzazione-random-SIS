# Minimizzazione random con SIS
Script python per minimizzare fsm, datapath e fsmd descritti in formato .blif tramite SIS.<br/>
### Funzionamento
Il programma prende in input il nome del file .blif da minimizzare, il numero di tentativi da eseguire,
il numero di comandi da eseguire per ogni tentativo e la modalità di minimizzazione (per area o per ritardo).<br/>
Durante l'esecuzione, per ogni tentativo, si crea un thread che genera un file di script con comandi di minimizzazione randomici, dopodiché
si confrontano i risultati ottenuti da ogni tentativo e viene tenuto il migliore, cancellando gli altri.<br/>
Alla fine dell'esecuzione si ottengono il file .blif con il circuito minimizzato e il file .script che ne ha permesso la creazione, entrambi 
nominati _min\_nomefile\_nodi\_letterali_.<br/>
Inoltre, verrà creato un file _sis\_we.txt_ contenente gli errori e i warning trascurabili generati da SIS.
### Esecuzione
```python3 minom.py -f file.blif -t num_tentativi -c num_comandi -m modalità```<br/>
Esempio 1: ```python3 minom.py -f fsm.blif -t 16 -c 256 -m a```<br/>
Esempio 2: ```python3 minom.py -f datapath.blif -t 32 -c 256 -m a```
#### Parametri
Per specificare il valore di un parametro è necessario utilizzare la rispettiva opzione
come mostrato negli esempi e di seguito<br/>
L'ordine in cui vengono specificati su linea di comando è irrilevante
* -f __file.blif__: nome del file da minimizzare con estensione .blif
* -t __num_tentativi__: numero di tentativi da eseguire (>=1)
* -c __num_comandi__: numero di comandi di minimizzazione che vengono eseguiti in ogni tentativo (>=1)
* -m __modalità__: può essere 'a' se si intende minimizzare per area, 'r' se per ritardo
### Note
-> Eseguire su macchina Linux con SIS installato<br/>
-> Per le fsm, ogni combinazione di comandi viene testata dopo assegnazione degli
stati sia con algoritmo _jedi_ che con algoritmo _nova_, quindi non deve essere specificata
la codifica degli stati nel file .blif<br/>
-> È necessario avere i file da minimizzare (e qualsiasi file con sotto-componenti) nella stessa
directory in cui si esegue lo script<br/>
-> Si consiglia di minimizzare una fsmd utilizzando come sotto-componenti
la fsm e il datapath già minimizzati<br/>
-> La terminazione manuale dell'esecuzione lascia nella directory i file precedentemente creati<br/>
-> In base ai parametri forniti e alla complessità del circuito da minimizzare, l'esecuzione dello script può richiedere anche diversi minuti
