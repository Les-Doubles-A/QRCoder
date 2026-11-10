# QRCoder

Dépôt GitHub : **https://github.com/Les-Doubles-A/QRCoder**

Générateur de QR Codes de bureau (customtkinter) : création en temps réel à partir de différents types de données.

<!-- installeur-release -->
## Installation

Téléchargez **`QRCoder-Setup-1.0.0.exe`** depuis la [dernière release](https://github.com/Les-Doubles-A/QRCoder/releases/latest), puis lancez-le.

L'installation se fait pour l'utilisateur courant, sans droits administrateur (par défaut dans `%LOCALAPPDATA%\Programs\QRCoder`), avec un raccourci dans le menu Démarrer et une désinstallation depuis les Paramètres Windows.

L'installeur n'est pas signé : si Windows SmartScreen l'affiche, cliquez sur « Informations complémentaires » puis « Exécuter quand même ».

### Recréer l'installeur

Compiler l'application (`pyinstaller QRCoder.spec`), puis lancer [Inno Setup 6](https://jrsoftware.org/isinfo.php) : `iscc installer\QRCoder.iss`. Le setup est créé dans `installer\Output\`.
