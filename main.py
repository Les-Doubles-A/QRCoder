"""
QRCoder - Générateur de QR Codes
====================================
Application de bureau moderne construite avec customtkinter permettant de
générer des QR Codes en temps réel à partir de différents types de données :
  - URL / Lien web
  - Texte libre
  - Configuration Wi-Fi
  - Contact (vCard)

Le QR Code généré est affiché instantanément et peut être exporté en PNG
haute qualité.

Auteur : QRCoder
"""

import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image


# ----------------------------------------------------------------------------
# Fonctions utilitaires
# ----------------------------------------------------------------------------

def resource_path(relative_path: str) -> str:
    """
    Retourne le chemin absolu vers une ressource (utile pour PyInstaller
    en mode --onefile, où les fichiers sont extraits dans un dossier
    temporaire référencé par sys._MEIPASS).
    """
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def escape_special_chars(value: str) -> str:
    """
    Échappe les caractères spéciaux réservés dans les formats Wi-Fi / vCard
    (norme QR Code) : le backslash, le point-virgule, la virgule et les
    deux-points doivent être précédés d'un backslash.
    """
    value = value.replace("\\", "\\\\")
    value = value.replace(";", "\\;")
    value = value.replace(",", "\\,")
    value = value.replace(":", "\\:")
    return value


# ----------------------------------------------------------------------------
# Classe principale de l'application
# ----------------------------------------------------------------------------

class QRCoderApp(ctk.CTk):
    """Fenêtre principale de l'application QRCoder."""

    # Types de données disponibles dans le menu déroulant
    DATA_TYPES = [
        "URL / Lien web",
        "Texte libre",
        "Configuration Wi-Fi",
        "Contact (vCard)",
    ]

    WIFI_SECURITY_OPTIONS = {
        "WPA / WPA2": "WPA",
        "WEP": "WEP",
        "Aucune (réseau ouvert)": "nopass",
    }

    def __init__(self):
        super().__init__()

        # ---------------- Configuration générale de la fenêtre ----------------
        self.title("QRCoder - Générateur de QR Codes")
        self.geometry("1000x640")
        self.minsize(880, 560)

        # Icône de la fenêtre (fonctionne sous Windows avec un .ico)
        try:
            icon_path = resource_path("QRCoder.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            # L'icône n'est pas bloquante si elle est absente ou non supportée (Linux/Mac)
            pass

        # ---------------- Variables d'état ----------------
        self.selected_type_var = ctk.StringVar(value=self.DATA_TYPES[0])
        self.current_qr_image = None  # Image PIL du QR Code généré (résolution d'aperçu)
        self.current_data_string = None  # Donnée textuelle encodée dans le dernier QR généré

        # Champs dynamiques (recréés selon le type sélectionné)
        self.field_vars = {}   # StringVar pour les champs simples (Entry, OptionMenu, Checkbox)
        self.field_widgets = {}  # Widgets nécessitant une lecture directe (ex: Textbox)

        # ---------------- Construction de l'interface ----------------
        self._build_layout()
        self._rebuild_input_fields()  # Construit les champs pour le type par défaut

    # ------------------------------------------------------------------
    # Construction de l'UI - structure générale
    # ------------------------------------------------------------------

    def _build_layout(self):
        """Construit la structure générale : panneau gauche (saisie) + panneau droit (aperçu)."""
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_control_panel()
        self._build_preview_panel()

    def _build_control_panel(self):
        """Panneau gauche : sélection du type de données + champs de saisie dynamiques."""
        panel = ctk.CTkScrollableFrame(self, width=380, corner_radius=12, label_text="Données à encoder")
        panel.grid(row=0, column=0, padx=(15, 8), pady=15, sticky="nsew")

        # ----- Titre -----
        title_label = ctk.CTkLabel(panel, text="QRCoder", font=ctk.CTkFont(size=26, weight="bold"))
        title_label.pack(anchor="w", padx=10, pady=(5, 15))

        # ----- Menu déroulant : type de données -----
        ctk.CTkLabel(panel, text="Type de données :", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=10
        )
        type_menu = ctk.CTkOptionMenu(
            panel, values=self.DATA_TYPES, variable=self.selected_type_var,
            command=lambda *_: self._rebuild_input_fields(),
        )
        type_menu.pack(fill="x", padx=10, pady=(5, 15))

        # ----- Conteneur des champs dynamiques -----
        self.dynamic_fields_container = ctk.CTkFrame(panel, fg_color="transparent")
        self.dynamic_fields_container.pack(fill="x", padx=0, pady=0)

        # ----- Bouton de génération -----
        generate_btn = ctk.CTkButton(
            panel, text="⚡ Générer le QR Code", command=self.generate_qr_code,
            fg_color="#1565c0", hover_color="#0d47a1",
        )
        generate_btn.pack(fill="x", padx=10, pady=(20, 8))

        # ----- Bouton d'exportation -----
        self.export_btn = ctk.CTkButton(
            panel, text="💾 Exporter en PNG (haute qualité)", command=self.export_qr_code,
            fg_color="#2e7d32", hover_color="#1b5e20", state="disabled",
        )
        self.export_btn.pack(fill="x", padx=10, pady=(0, 10))

    def _build_preview_panel(self):
        """Panneau droit : aperçu du QR Code généré."""
        container = ctk.CTkFrame(self, corner_radius=12)
        container.grid(row=0, column=1, padx=(8, 15), pady=15, sticky="nsew")
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            container, text="Aperçu du QR Code", font=ctk.CTkFont(size=18, weight="bold")
        )
        header.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        self.preview_frame = ctk.CTkFrame(container, fg_color=("gray90", "gray17"), corner_radius=12)
        self.preview_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.preview_frame.grid_rowconfigure(0, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(
            self.preview_frame, text="Aucun QR Code généré.\nRemplissez les champs puis cliquez sur « Générer ».",
            text_color="gray", justify="center",
        )
        self.preview_label.grid(row=0, column=0)

    # ------------------------------------------------------------------
    # Construction des champs dynamiques selon le type sélectionné
    # ------------------------------------------------------------------

    def _clear_dynamic_fields(self):
        """Supprime tous les widgets du conteneur de champs dynamiques."""
        for widget in self.dynamic_fields_container.winfo_children():
            widget.destroy()
        self.field_vars = {}
        self.field_widgets = {}

    def _rebuild_input_fields(self):
        """Reconstruit les champs de saisie en fonction du type de données choisi."""
        self._clear_dynamic_fields()
        data_type = self.selected_type_var.get()

        if data_type == "URL / Lien web":
            self._build_url_fields()
        elif data_type == "Texte libre":
            self._build_text_fields()
        elif data_type == "Configuration Wi-Fi":
            self._build_wifi_fields()
        elif data_type == "Contact (vCard)":
            self._build_contact_fields()

    def _labeled_entry(self, parent, label_text, key, placeholder=""):
        """Crée un couple Label + Entry, enregistre la variable dans self.field_vars."""
        ctk.CTkLabel(parent, text=label_text).pack(anchor="w", padx=10, pady=(8, 0))
        var = ctk.StringVar(value="")
        entry = ctk.CTkEntry(parent, textvariable=var, placeholder_text=placeholder)
        entry.pack(fill="x", padx=10, pady=(2, 0))
        self.field_vars[key] = var
        return entry

    def _build_url_fields(self):
        parent = self.dynamic_fields_container
        self._labeled_entry(parent, "Adresse URL :", "url", "ex: https://exemple.com")

    def _build_text_fields(self):
        parent = self.dynamic_fields_container
        ctk.CTkLabel(parent, text="Texte à encoder :").pack(anchor="w", padx=10, pady=(8, 0))
        textbox = ctk.CTkTextbox(parent, height=140)
        textbox.pack(fill="x", padx=10, pady=(2, 0))
        self.field_widgets["text"] = textbox

    def _build_wifi_fields(self):
        parent = self.dynamic_fields_container
        self._labeled_entry(parent, "Nom du réseau (SSID) :", "ssid", "ex: MonReseauWifi")

        ctk.CTkLabel(parent, text="Type de sécurité :").pack(anchor="w", padx=10, pady=(8, 0))
        security_var = ctk.StringVar(value=list(self.WIFI_SECURITY_OPTIONS.keys())[0])
        security_menu = ctk.CTkOptionMenu(parent, values=list(self.WIFI_SECURITY_OPTIONS.keys()), variable=security_var)
        security_menu.pack(fill="x", padx=10, pady=(2, 0))
        self.field_vars["security"] = security_var

        self._labeled_entry(parent, "Mot de passe :", "password", "Laisser vide si réseau ouvert")

        hidden_var = ctk.BooleanVar(value=False)
        hidden_checkbox = ctk.CTkCheckBox(parent, text="Réseau caché (SSID non diffusé)", variable=hidden_var)
        hidden_checkbox.pack(anchor="w", padx=10, pady=(12, 0))
        self.field_vars["hidden"] = hidden_var

    def _build_contact_fields(self):
        parent = self.dynamic_fields_container
        self._labeled_entry(parent, "Nom complet :", "name", "ex: Jean Dupont")
        self._labeled_entry(parent, "Téléphone :", "phone", "ex: +33612345678")
        self._labeled_entry(parent, "E-mail :", "email", "ex: jean.dupont@mail.com")
        self._labeled_entry(parent, "Organisation (optionnel) :", "organization", "ex: Ma Société")

    # ------------------------------------------------------------------
    # Construction de la donnée à encoder selon le type sélectionné
    # ------------------------------------------------------------------

    def build_data_string(self) -> str:
        """
        Construit la chaîne de caractères à encoder dans le QR Code,
        selon le type de données actuellement sélectionné.
        Lève une ValueError si des champs obligatoires sont manquants.
        """
        data_type = self.selected_type_var.get()

        if data_type == "URL / Lien web":
            url = self.field_vars["url"].get().strip()
            if not url:
                raise ValueError("Veuillez saisir une adresse URL.")
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "https://" + url
            return url

        if data_type == "Texte libre":
            text = self.field_widgets["text"].get("1.0", "end").strip()
            if not text:
                raise ValueError("Veuillez saisir un texte à encoder.")
            return text

        if data_type == "Configuration Wi-Fi":
            ssid = self.field_vars["ssid"].get().strip()
            if not ssid:
                raise ValueError("Veuillez saisir le nom du réseau (SSID).")
            security_label = self.field_vars["security"].get()
            security_code = self.WIFI_SECURITY_OPTIONS.get(security_label, "WPA")
            password = self.field_vars["password"].get()
            hidden = self.field_vars["hidden"].get()

            if security_code != "nopass" and not password:
                raise ValueError("Veuillez saisir un mot de passe ou choisir « Aucune (réseau ouvert) ».")

            ssid_escaped = escape_special_chars(ssid)
            password_escaped = escape_special_chars(password) if security_code != "nopass" else ""
            hidden_str = "true" if hidden else "false"

            if security_code == "nopass":
                return f"WIFI:S:{ssid_escaped};T:nopass;H:{hidden_str};;"
            return f"WIFI:S:{ssid_escaped};T:{security_code};P:{password_escaped};H:{hidden_str};;"

        if data_type == "Contact (vCard)":
            name = self.field_vars["name"].get().strip()
            phone = self.field_vars["phone"].get().strip()
            email = self.field_vars["email"].get().strip()
            organization = self.field_vars["organization"].get().strip()

            if not name and not phone and not email:
                raise ValueError("Veuillez renseigner au moins le nom, le téléphone ou l'e-mail.")

            lines = ["BEGIN:VCARD", "VERSION:3.0"]
            if name:
                lines.append(f"FN:{escape_special_chars(name)}")
            if organization:
                lines.append(f"ORG:{escape_special_chars(organization)}")
            if phone:
                lines.append(f"TEL:{escape_special_chars(phone)}")
            if email:
                lines.append(f"EMAIL:{escape_special_chars(email)}")
            lines.append("END:VCARD")
            return "\n".join(lines)

        raise ValueError("Type de données inconnu.")

    # ------------------------------------------------------------------
    # Génération et affichage du QR Code
    # ------------------------------------------------------------------

    def _make_qr_image(self, data: str, box_size: int = 10, border: int = 4) -> Image.Image:
        """Génère une image PIL de QR Code pour la donnée fournie."""
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_H,  # Haute tolérance aux erreurs (jusqu'à 30%)
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white")
        return image.convert("RGB")

    def generate_qr_code(self):
        """Récupère les données saisies, génère le QR Code et l'affiche dans l'aperçu."""
        try:
            data = self.build_data_string()
        except ValueError as e:
            messagebox.showwarning("QRCoder", str(e))
            return

        try:
            qr_image = self._make_qr_image(data, box_size=10, border=4)
        except Exception as e:
            messagebox.showerror("QRCoder - Erreur", f"Impossible de générer le QR Code :\n{e}")
            return

        self.current_qr_image = qr_image
        self.current_data_string = data

        # Affichage dans l'aperçu (redimensionné pour tenir dans le panneau)
        preview_size = 340
        ctk_image = ctk.CTkImage(light_image=qr_image, dark_image=qr_image, size=(preview_size, preview_size))
        self.preview_label.configure(image=ctk_image, text="")
        self.preview_label.image = ctk_image  # Empêche le garbage collector de libérer l'image

        self.export_btn.configure(state="normal")

    # ------------------------------------------------------------------
    # Exportation en PNG haute qualité
    # ------------------------------------------------------------------

    def export_qr_code(self):
        """Sauvegarde le QR Code actuel en PNG haute résolution."""
        if not self.current_data_string:
            messagebox.showwarning("QRCoder", "Veuillez d'abord générer un QR Code.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Exporter le QR Code",
            defaultextension=".png",
            filetypes=[("Image PNG", "*.png")],
            initialfile="qrcode.png",
        )
        if not file_path:
            return

        try:
            # Régénération à haute résolution (box_size plus grand) pour une exportation nette
            high_res_image = self._make_qr_image(self.current_data_string, box_size=25, border=4)
            high_res_image.save(file_path, format="PNG")
        except Exception as e:
            messagebox.showerror("QRCoder - Erreur", f"Impossible d'exporter le QR Code :\n{e}")
            return

        messagebox.showinfo("QRCoder", f"QR Code exporté avec succès :\n{file_path}")


# ----------------------------------------------------------------------------
# Point d'entrée
# ----------------------------------------------------------------------------

def main():
    # Thème adaptatif : suit automatiquement le mode clair/sombre du système
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = QRCoderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
