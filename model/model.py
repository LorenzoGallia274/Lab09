from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO

class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """


        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        # TODO
        # chiedo al db tutte le associazioni tra escursioni e punti di nteresse
        associazioni = EscursioneDAO.get_escursioni_punti_interesse()
        # se la query è andata a buon fine
        if associazioni is not None:
            # scorro ogni associazione (coppia id) (relazione)
            for associazione in associazioni:
                # estraggo gli id
                id_escursione = associazione['id_escursione']
                id_punto_interesse = associazione['id_punto_interesse']
                # creo oggetti (escursione e punto_interesse) tramite il loro dizionario
                # prendono come id, quelli estratti a riga 51/52
                escursione = self.escursioni_map[id_escursione]
                punto_interesse = self.punti_interesse_map[id_punto_interesse]
                # collego il punto di interesse all'escursione (e viceversa), aggiungendoli ai rispettivi set
                escursione.punti_interesse.add(punto_interesse)
                punto_interesse.escursioni.add(escursione)






    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1
        # TODO
        # lista vuota che conterrà le escursioni appartenenti al parco scelto dall'utente
        self.l_escursioni = []
        # scorro tutti gli oggetti escursione
        for e in self.escursioni_map.values():
            # filtro e salvo solo le escursioni del parco selezionato
            if e.id_parco == id_parco:
                self.l_escursioni.append(e)
        # salvo i vincoli dentro il model (self.) per usarli nella ricorsione
        self.max_giorni = max_giorni
        self.max_budget = max_budget
        # chiamo la ricorsione e avvio l'algoritmo partendo da zero e tutti contenitori vuoti
        self._ricorsione(0,[],0,0,0,set())



        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno
        # A: controlla sempre il valore corrente ha superato il miglior valore trovato fino ad ora
        if valore_corrente > self._valore_ottimo:
            # aggiorno e copio
            self._valore_ottimo = valore_corrente
            self._costo = costo_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()
        # scorro le escursioni rimanenti da start index in poi
        for i in range(start_index,len(self.l_escursioni)):
            # escursione candidata
            escursione_iesima = self.l_escursioni[i]
            # C: vincolo 1
            # se è stato impostato un limite di giorni non deve sforarlo (scarta l'escursione se supera la durata massima)
            if self.max_giorni is not None:
                if durata_corrente + escursione_iesima.durata_giorni > self.max_giorni:
                    continue
            #vincolo 2
            # se è stato impostato un budget non deve sforarlo (scarta l'escursione se supera il budget massimo)
            if self.max_budget is not None:
                if costo_corrente + escursione_iesima.costo > self.max_budget:
                        continue
            # vincolo 3
            # scarto l'escursione se contiene almeno un punto di interesse già visitato
            if len(escursione_iesima.punti_interesse.intersection(punti_usati)) > 0:
                    continue
            # D : aggiungo al pacchetto parziale l'escursione valida (superati i vincoli)
            pacchetto_parziale.append(escursione_iesima)
            # aggiungo tutti i punti di interesse di questa escursione all'insieme di quelli già visitati
            punti_usati.update(escursione_iesima.punti_interesse)
            # sommo i voti dei punti di interesse della singola escursione
            somma_voti = 0
            for p in escursione_iesima.punti_interesse:
                somma_voti += p.voto_visitatori
            # E : chiamo la ricorsione
            self._ricorsione(i+1,
                             pacchetto_parziale,
                             durata_corrente+escursione_iesima.durata_giorni,
                             costo_corrente+escursione_iesima.costo,
                             valore_corrente+somma_voti,
                             punti_usati)
            # F backtracking
            # rimuovo l'ultima escursione aggiunta
            pacchetto_parziale.pop()
            # rimuovo i punti di interesse di quell'escursione dall'insieme dei punti usati
            punti_usati.difference_update(escursione_iesima.punti_interesse)









