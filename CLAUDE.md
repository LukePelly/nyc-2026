# Itinerario New York 2026

Sito pubblico: https://lukepelly.github.io/nyc-2026/ (GitHub Pages dal branch `main`, cartella radice).
Tutto l'itinerario sta in `index.html`. Durante il viaggio (28/10 – 4/11) questo repo è l'unica fonte aggiornata: il PC di casa è spento.

## Come pubblicare una modifica

1. `git pull` prima di toccare qualsiasi cosa: ogni mattina una GitHub Action committa il meteo.
2. Modifica `index.html`.
3. Commit e push **direttamente su `main`**. Niente branch, niente pull request: il sito si aggiorna solo da `main`, in circa un minuto.
4. Se il push viene rifiutato, `git pull --rebase` e ripeti il push.

Se in questa sessione è disponibile il tool Artifact, ripubblica anche l'artifact https://claude.ai/artifact/U5aYRkYsVmuEdZFoqmbAyu (leggilo prima con `action: "read"`, poi pubblica `index.html` su quell'URL). Se non c'è, salta: lo riallinea Luca al rientro.

## Cose da non toccare

- Il blocco tra `/*METEO:START*/` e `/*METEO:END*/` lo riscrive `meteo.py` tramite `.github/workflows/meteo.yml` (ogni giorno alle 07:00 di New York, lanciabile a mano da Actions → Meteo → Run workflow). Non modificarlo a mano.
- Se cambia il programma di un giorno, aggiorna anche la sua voce nell'array `RAINB` (piano B se piove).

## Regole sul contenuto

- Si gira solo col passeggino (Babyzen YOYO). Mai suggerire il marsupio. Percorsi adatti a ruote piccole, meglio ascensori; se il passeggino non passa: bimbo in braccio e YOYO a spalla.
- Niente rientri in hotel durante il giorno, nemmeno sabato 31/10 (deciso quella mattina: pisolino in passeggino a Madison Square Park). Il bimbo dorme nel passeggino. Niente buchi vuoti nelle giornate: riempili con passeggiate o soste al chiuso vicine al percorso. Niente Met.
- Ristoranti e pasti sono per gli adulti: non aggiungere note su cosa mangia il bimbo. Le note "bimbo" riguardano solo logistica (sonno, passeggino, fasciatoio).
- Il repo è pubblico: non aggiungere dati personali oltre a quelli già presenti (niente numeri di prenotazione, telefoni, documenti).
- Scrivi in italiano, tono asciutto, niente trattini lunghi.
