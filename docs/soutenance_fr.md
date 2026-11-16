# Soutenance CAIRN — script, questions du jury, guide de démonstration (FR)

> Document de travail pour Amal Karaoud. Le texte oral par diapositive est aussi dans les **notes du PowerPoint**.

## 1. Répartition du temps (15 min maximum)
| Diapo | Contenu | Durée |
|---|---|---|
| 1 | Titre | 0:15 |
| 2 | Problème et justification | 1:15 |
| 3 | État de l'art | 1:00 |
| 4 | Composants | 0:45 |
| 5 | Montage | 0:45 |
| 6 | Architecture | 1:00 |
| 7 | Cours exploité | 0:45 |
| 8 | Code | 1:15 |
| 9 | Menaces / limites | 0:45 |
| 10 | **Démonstration** | 3:00 |
| 11 | Résultats | 1:00 |
| 12 | Conclusion | 0:45 |
| | **Total** | **12:30** (marge 2:30) |
Si tu es en retard : coupe la diapo 7 (réponds oralement si on te la demande) puis raccourcis la 3.

## 2. À faire AVANT la soutenance (≈ 15 min, indispensable)
1. Importer le projet dans Wokwi (`docs/WOKWI_GUIDE.md`) et vérifier qu'il démarre. **Cette vérification n'a pas été faite pour toi** : les noms de pièces et de broches de `diagram.json` viennent d'exemples publics.
2. Prendre : une capture du circuit (diapo 5), une capture de la simulation avec l'OLED (diapo 10).
3. Faire un **export de secours** : lancer la démo, appuyer ATTACK puis AUDIT, copier le terminal dans `dump.txt`, noter la ligne `ANCHOR`.
4. Enregistrer une courte vidéo d'écran de la démo (plan B).

## 3. Scénario de démonstration (3 min)
| # | Action | Résultat attendu |
|---|---|---|
| 1 | Lancer ▶ | OLED « CHAIN:OK », LED verte, lignes `EVT` dans le terminal |
| 2 | Curseur gaz > seuil (2000), cliquer le PIR, DHT22 +10 °C | événements GAS_ALARM, MOTION, TEMP_JUMP ; LED rouge ; l'ancre s'affiche tous les 10 enregistrements |
| 3 | ATTACK (1ʳᵉ fois = EDIT) puis AUDIT | OLED « BROKEN @n HASH_ » (observé sur hôte : HASH_MISMATCH) |
| 4 | Relancer, ATTACK ×4 (REHASH) puis AUDIT | l'audit embarqué peut afficher **OK** (observé sur hôte) |
| 5 | Copier le terminal → `verify.py` | « TAMPERING DETECTED … MAC_MISMATCH » |
Commande : `python3 tools/verify.py --log dump.txt --key-hex 434149524e2d44454d4f2d4b45592d4e4f542d412d5345435245542d30303030 --anchor <n>:<hash>`
Les résultats des étapes 3 à 5 ont été **observés sur ordinateur hôte**, pas encore dans Wokwi.
Message à dire : « l'audit embarqué n'est pas une ancre de confiance ; la preuve vient de la clé et de l'ancre gardées hors de la carte ».

**Plan B** : (a) vidéo préenregistrée ; (b) captures ; (c) exécuter `verify.py` sur `dump.txt` ; (d) `python3 -m unittest discover -s tests -v` (16 tests) pour montrer que la logique fonctionne.

## 4. Questions probables et réponses
1. **Pourquoi MicroPython est-il central ?** Tout le firmware est en MicroPython : GPIO, ADC, I²C, Wi-Fi/NTP du cours, plus `hashlib` et `framebuf` en extension. HMAC n'existe pas en MicroPython : je l'ai écrit (RFC 2104, testé contre la bibliothèque standard et un vecteur RFC 4231).
2. **Est-ce nouveau ?** Non. Le chaînage de hachages et le MAC à clé évolutive datent de Schneier & Kelsey (1999). Mon apport est une adaptation (MicroPython, filtre de plausibilité avant scellement, démo reproductible). Ma recherche était limitée : je ne peux pas exclure l'existence d'un équivalent.
3. **Pourquoi un hachage ET un HMAC ?** Le hachage se vérifie sans clé (audit embarqué) mais un attaquant peut le recalculer. Le HMAC exige la clé, gardée hors de la carte.
4. **À quoi sert le cliquet de clé ?** Après un vol de la carte, on ne peut pas falsifier les enregistrements antérieurs, car leurs clés ont été effacées.
5. **Que se passe-t-il si on supprime la fin du journal ?** Indétectable seul ; détecté avec une ancre (n°, empreinte) conservée ailleurs, ou par l'empreinte en RAM tant que la carte est alimentée.
6. **Et si l'attaquant vole la clé courante ?** Il peut ajouter de faux événements futurs ; limite connue, il faudrait un élément sécurisé.
7. **Les résultats viennent-ils de Wokwi ?** Non : données synthétiques, exécutées sur ordinateur (graine fixe). Ils montrent que l'implémentation se comporte comme conçue, pas des performances ESP32.
8. **Pourquoi 100 % partout ?** Ce sont des propriétés déterministes de la construction ; ce n'est pas une performance statistique. Les cas à 0 % sont tout aussi importants.
9. **Faux positifs ?** Sur 37 500 échantillons de gaz propres : 13 alarmes, soit environ 0,035 %. Réglage fait sur données synthétiques ; des capteurs réels demanderaient un recalibrage.
10. **Pourquoi deux règles pour le gaz ?** Le seuil fixe (TP2) rate un pic à 1200 ; le détecteur adaptatif rate une montée lente. Elles sont complémentaires.
11. **Pourquoi Wokwi ?** Je n'ai pas de carte ; l'enseignante a accepté Wokwi. Les pièces PIR, MQ-2, DHT22, SSD1306 y existent.
12. **Pourquoi GPIO27 pour le bouton ?** GPIO12 est une broche de démarrage de l'ESP32.
13. **Que ferais-tu avec plus de temps ?** Rotation du journal, ancre par e-mail (chapitre 5), mesures sur ESP32 réel.
14. **Limites de la flash ?** Chaque enregistrement réécrit l'état : usure ; non traité en v0.1.
15. **L'horloge NTP est-elle fiable ?** Non authentifiée : l'horodatage est indicatif, le numéro de séquence fait foi.
