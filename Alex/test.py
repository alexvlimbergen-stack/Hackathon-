import os
import customtkinter as ctk
from tkinter import filedialog
from sim_checker import main



# --- CONFIGURATIE ---
DATABASE_MAP = r"C:\Users\alexv_f6kqdbo\OneDrive - KU Leuven\Documents\Hackathon\Hackathon-\database"

# Stel het thema in (opties: "dark", "light", "system")
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class GatekeeperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Venster instellingen
        self.title("HR Database Gatekeeper")
        self.geometry("600x500")
        self.resizable(False, False)

        # ---- UI ELEMENTEN ----
        # Titel
        self.title_label = ctk.CTkLabel(self, text="HR Document Gatekeeper", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=20)

        # Instructie
        self.info_label = ctk.CTkLabel(self, text="Selecteer een nieuw contract om te vergelijken met de database.", font=ctk.CTkFont(size=13))
        self.info_label.pack(pady=5)

        # Upload Knop
        self.upload_btn = ctk.CTkButton(self, text="📁 Selecteer & Controleer Bestand", command=self.open_file_picker, font=ctk.CTkFont(size=14, weight="bold"), height=40)
        self.upload_btn.pack(pady=20)

        # Geselecteerd bestand label
        self.file_label = ctk.CTkLabel(self, text="Geen bestand geselecteerd", font=ctk.CTkFont(size=12), text_color="gray")
        self.file_label.pack(pady=5)

        # Resultaten Frame (Inclusief grote status-badge)
        self.result_frame = ctk.CTkFrame(self, width=520, height=260)
        self.result_frame.pack(pady=20, padx=40, fill="both", expand=True)
        self.result_frame.pack_propagate(False)

        # Status Badge (COEXIST / REPLACE)
        self.status_badge = ctk.CTkLabel(self.result_frame, text="WACHTEND OP BESTAND", font=ctk.CTkFont(size=18, weight="bold"), text_color="white", fg_color="#5a5a5a", corner_radius=8, height=40, width=200)
        self.status_badge.pack(pady=15)

        # Details Textbox (Scrollbaar voor je logging/redenen)
        self.details_box = ctk.CTkTextbox(self.result_frame, font=ctk.CTkFont(size=12), activate_scrollbars=True)
        self.details_box.pack(pady=10, padx=15, fill="both", expand=True)
        self.details_box.insert("0.0", "De resultaten van de database-controle verschijnen hier...")
        self.details_box.configure(state="disabled")

    def open_file_picker(self):
        """Opent de verkenner om een bestand te kiezen."""
        geselecteerd_pad = filedialog.askopenfilename(
            title="Selecteer een contract",
            filetypes=[("Text bestanden", "*.txt"), ("PDF bestanden", "*.pdf"), ("Alle bestanden", "*.*")]
        )

        if geselecteerd_pad:
            filename = os.path.basename(geselecteerd_pad)
            self.file_label.configure(text=f"Geanalyseerd: {filename}", text_color="#1f538d")
            self.voer_jouw_logica_uit(geselecteerd_pad)

    def voer_jouw_logica_uit(self, nieuw_bestand_pad):
        """Hier activeer je jouw eigen vergelijkingscode."""
        
        # Maak het tekstveld leeg voor nieuwe resultaten
        self.details_box.configure(state="normal")
        self.details_box.delete("0.0", "end")
        
        # 1. Loop door je database map (jouw logica)
        database_bestanden = [f for f in os.listdir(DATABASE_MAP) if f.endswith('.txt') or f.endswith('.pdf')]
        
        # Dummy variabelen om te laten zien hoe de GUI reageert
        # Vervang deze logica door jouw AI/Similarity checker uitkomst!
        eind_beslissing = "COEXIST"  # Verander naar "REPLACE" op basis van jouw code
        log_output = f"Analyse gestart voor: {os.path.basename(nieuw_bestand_pad)}\n"
        log_output += f"Database bevat {len(database_bestanden)} bestanden.\n"
        log_output += "-" * 50 + "\n"
        self.status_badge.configure(
            text="✅ COEXIST", 
            fg_color="#007A33",  # Groen
            text_color="white"
                    )
        for db_bestand in database_bestanden:
            db_bestand_pad = os.path.join(DATABASE_MAP, db_bestand)
            
            # ==========================================================
            # JOUW CODE HIER: 
            # Vergelijk 'nieuw_bestand_pad' met 'db_bestand_pad'
            # ==========================================================

            result = main(nieuw_bestand_pad,db_bestand_pad)
            
            # Voorbeeld log-regel per bestand (pas dit aan):
            if result =='exact copy found':
                log_output += f"• Vergeleken met {db_bestand} -> EXACTE COPY ( match)\n"     
                eind_beslissing == 'REPLACE'
                self.status_badge.configure(
                    text="❌ REPLACE", 
                    fg_color="#A30000",  # Rood
                    text_color="white"
                    )
                

            else:
                log_output += f"• Vergeleken met {db_bestand} -> OK (Geen match)\n"

        # Update de scrollbox met jouw resultaten/redenen
        self.details_box.insert("0.0", log_output)
        self.details_box.configure(state="disabled")

        # 2. Update de visuele status-badge op basis van de einduitslag
            
        
            

if __name__ == "__main__":
    app = GatekeeperApp()
    app.mainloop()
