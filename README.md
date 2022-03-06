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
```python3 minom.py file.blif num_tentativi num_comandi modalità```<br/>
Esempio 1: ```python3 minom.py fsm.blif 16 256 a```
Esempio 2: ```python3 minom.py datapath.blif 32 256 a```
* __file.blif__: nome del file da minimizzare con estensione .blif
* __num_tentativi__: numero di tentativi da eseguire (>=1)
* __num_comandi__: numero di comandi di minimizzazione che vengono eseguiti in ogni tentativo (>=1)
* __modalità__: può essere 'a' se si intende minimizzare per area, 'r' se per ritardo
### Note
-> Eseguire su macchina Linux con SIS installato<br/>
-> Per le fsm, ogni combinazione di comandi viene testata dopo assegnazione degli
stati sia con algoritmo _jedi_ che con algoritmo _nova_<br/>
-> È necessario avere i file da minimizzare (e qualsiasi file con sotto-componenti) nella stessa
directory in cui si esegue lo script<br/>
-> Si consiglia di minimizzare una fsmd utilizzando come sotto-componenti
la fsm e il datapath già minimizzati<br/>
-> La terminazione manuale dell'esecuzione lascia nella directory i file precedentemente creati<br/>
-> In base ai parametri forniti e alla complessità del circuito da minimizzare, l'esecuzione dello script può richiedere anche diversi minuti
