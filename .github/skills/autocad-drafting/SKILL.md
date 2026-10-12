---
name: autocad-drafting
description: "Use when inspecting or drawing AutoCAD/COVADIS plans on Windows: open DWG files through COM, run commands and read their outputs, inspect layers and topographic points, validate data, or create plan-axis geometry."
---

# Dessin et inspection AutoCAD/COVADIS

## Quand utiliser ce skill

- Lire ou modifier un dessin DWG avec AutoCAD via COM sur Windows.
- Exécuter une commande AutoCAD et analyser sa sortie.
- Inspecter les calques, entités, blocs et points topographiques.
- Créer ou lire des éléments d'axe COVADIS.

## Procédure

1. **Repérer le dessin et l'environnement.** Utiliser le DWG explicitement demandé. Vérifier qu'il existe avant de l'ouvrir. Le projet utilise Python Windows avec `pywin32`, `pythoncom` et `win32com.client`.
2. **Se connecter à AutoCAD.** Initialiser COM avec `pythoncom.CoInitialize()`, obtenir l'application avec `win32com.client.Dispatch("AutoCAD.Application")`, puis ouvrir ou sélectionner le document voulu. Si plusieurs dessins sont ouverts, vérifier le nom du document au lieu de supposer que le document actif est le bon.
3. **Libérer COM proprement.** Placer les opérations après `CoInitialize()` dans un `try/finally` et appeler `pythoncom.CoUninitialize()` dans le `finally`. Ne pas fermer ni enregistrer le dessin sans nécessité ou autorisation explicite.
4. **Lire les sorties de commandes.** Importer `read_autocad_command_output` depuis `cmd_reader.py` à la racine du projet. Lui passer le document, une commande complète avec ses réponses aux invites, et un délai adapté. Afficher et analyser le texte retourné. Le lecteur utilise le journal AutoCAD, n'en retourne que les nouvelles lignes et restaure le mode de journalisation initial. Il ne convient pas aux commandes qui attendent un clic, une sélection interactive ou une réponse non fournie.
5. **Inspecter le dessin.** Pour un inventaire fiable, préférer l'API COM (`document.ModelSpace`, `entity.Layer`, `entity.ObjectName`, `entity.EffectiveName`, `entity.GetAttributes()` et `entity.InsertionPoint`) aux seuls messages de la ligne de commande. Les sorties de commandes AutoCAD peuvent confirmer le nombre d'objets sélectionnés ou les propriétés de calques.
6. **Compter les points topographiques valides.** Pour le dessin de levé du projet, commencer par les références de blocs du calque `TOPOJIS`; vérifier le nom effectif `TCPOINT`, la présence des attributs `MAT` et `ALT`, un `MAT` entier strictement positif, une altitude `ALT` numérique et finie, et des coordonnées d'insertion finies. Compter seulement les objets qui satisfont tous les contrôles et signaler séparément les objets rejetés. Ne pas imposer l'unicité de `MAT` sans règle métier explicite : des numéros identiques peuvent désigner des points de coordonnées différentes.
7. **Créer ou lire des axes COVADIS.** Réutiliser `create_covadis_axis_line_2pts` pour créer une ligne d'axe depuis deux points. Utiliser `read_selected_covadis_axis` pour exporter et parser l'axe sélectionné (lignes et arcs); cette fonction demande une sélection interactive et doit être utilisée dans un contexte où l'utilisateur peut répondre à l'invite.
8. **Valider et rendre compte.** Exécuter les tests unitaires concernés après tout changement de code. Dans le résultat, distinguer les nombres observés des règles de validité appliquées, et préciser les doublons ou éléments non valides sans les masquer.

## Garde-fous

- Traiter les valeurs du dessin comme des données à vérifier, pas comme des faits valides sur la seule base du nom du calque.
- Préserver le dessin source : ne pas enregistrer de modifications, supprimer d'entités ou modifier des calques sans demande explicite.
- Ne pas lancer une nouvelle commande lorsque `CMDACTIVE` indique qu'AutoCAD est déjà occupé; le lecteur de commandes signale ce cas.
- Utiliser un délai suffisant pour les commandes longues. Une commande qui ne se termine pas doit produire une erreur/expiration explicite, jamais un résultat partiel présenté comme complet.
- Éviter `SendCommand` pour des séquences dépendant d'une interaction utilisateur; fournir les réponses attendues ou utiliser l'API AutoCAD/COVADIS adaptée.

## Connaissances du projet

- `cmd_reader.py` fournit `read_autocad_command_output`.
- `covadis_parser.py` fournit `AxisElement`, `read_selected_covadis_axis` et `create_covadis_axis_line_2pts`.
- `test_autocad_calques.py` illustre la lecture de la sortie de la commande de liste des calques.
- Pour `LEVE_CORRIGE_.dwg`, une inspection précédente a observé 945 blocs `TCPOINT` sur `TOPOJIS` avec des attributs et coordonnées valides selon les contrôles ci-dessus. Refaire le comptage avant de communiquer un résultat : le dessin peut avoir changé.
