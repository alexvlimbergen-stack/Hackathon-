import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB_PAD = "bestanden.db"

STANDAARD_ONDERWERPEN = [
    "Werk",
    "School",
    "Financiën",
    "Persoonlijk",
    "Overig"
]

LAATSTE_ONDERWERP = "Overig"


def init_db():
    with sqlite3.connect(DB_PAD) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS onderwerpen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                naam TEXT NOT NULL UNIQUE
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS bestanden (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pad TEXT NOT NULL,
                onderwerp_id INTEGER NOT NULL REFERENCES onderwerpen(id),
                status TEXT NOT NULL,
                betrouwbaarheid INTEGER NOT NULL
                    CHECK (betrouwbaarheid BETWEEN 1 AND 10),
                toegevoegd TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        for naam in STANDAARD_ONDERWERPEN:
            con.execute(
                "INSERT OR IGNORE INTO onderwerpen (naam) VALUES (?)",
                (naam,)
            )


def haal_onderwerpen():
    with sqlite3.connect(DB_PAD) as con:
        namen = [
            rij[0]
            for rij in con.execute("SELECT naam FROM onderwerpen")
        ]

    return sorted(
        namen,
        key=lambda n: (n == LAATSTE_ONDERWERP, n.lower())
    )


def opslaan(pad, onderwerp, status, betrouwbaarheid):
    with sqlite3.connect(DB_PAD) as con:

        con.execute(
            "INSERT OR IGNORE INTO onderwerpen (naam) VALUES (?)",
            (onderwerp,)
        )

        onderwerp_id = con.execute(
            "SELECT id FROM onderwerpen WHERE naam = ?",
            (onderwerp,)
        ).fetchone()[0]

        con.execute(
            """
            INSERT INTO bestanden
            (pad, onderwerp_id, status, betrouwbaarheid)
            VALUES (?, ?, ?, ?)
            """,
            (
                pad,
                onderwerp_id,
                status,
                int(betrouwbaarheid)
            )
        )


def _stel_stijl_in(root):
    stijl = ttk.Style(root)

    stijl.theme_use("clam")

    achtergrond = "#f5f5f5"
    tekst = "#1f1f1f"

    root.configure(bg=achtergrond)

    stijl.configure(
        ".",
        background=achtergrond,
        foreground=tekst,
        font=("Segoe UI", 10)
    )

    stijl.configure(
        "Title.TLabel",
        font=("Segoe UI", 16, "bold")
    )

    stijl.configure(
        "File.TLabel",
        font=("Segoe UI", 11, "bold")
    )

    stijl.configure(
        "Muted.TLabel",
        foreground="#6b7280",
        font=("Segoe UI", 9)
    )

    stijl.configure(
        "Question.TLabel",
        font=("Segoe UI", 13)
    )

    stijl.configure(
        "Value.TLabel",
        font=("Segoe UI", 16, "bold")
    )

    stijl.configure(
        "TLabelframe.Label",
        font=("Segoe UI", 10, "bold")
    )

    stijl.configure(
        "Big.TButton",
        font=("Segoe UI", 11, "bold"),
        padding=(26, 10)
    )


def _centreer(root):
    root.update_idletasks()

    breedte = root.winfo_width()
    hoogte = root.winfo_height()

    x = (root.winfo_screenwidth() - breedte) // 2
    y = (root.winfo_screenheight() - hoogte) // 3

    root.geometry(f"+{x}+{y}")


def toon_popup(bestandspad):
    opgeslagen = {"waarde": False}

    root = tk.Tk()

    root.title("Review File")
    root.geometry("560x500")
    root.minsize(560, 500)
    root.maxsize(560, 500)
    root.resizable(False, False)
    root.attributes("-topmost", True)

    _stel_stijl_in(root)

    hoofd = ttk.Frame(root, padding=20)
    hoofd.pack(fill="both", expand=True)

    stap_label = ttk.Label(
        hoofd,
        text="Step 1 of 2",
        style="Muted.TLabel"
    )
    stap_label.pack(anchor="w")

    ttk.Label(
        hoofd,
        text="Review File",
        style="Title.TLabel"
    ).pack(anchor="w", pady=(0, 12))

    bestandkaart = ttk.Frame(hoofd)
    bestandkaart.pack(fill="x", pady=(0, 12))

    ttk.Label(
        bestandkaart,
        text="📄 " + os.path.basename(bestandspad),
        style="File.TLabel"
    ).pack(anchor="w")

    ttk.Label(
        bestandkaart,
        text=bestandspad,
        style="Muted.TLabel",
        wraplength=500
    ).pack(anchor="w")

    ttk.Separator(hoofd).pack(fill="x", pady=(0, 20))

    #################################################################
    # STAP 1
    #################################################################

    stap1 = ttk.Frame(hoofd)
    stap1.pack(fill="both", expand=True)

    ttk.Label(
        stap1,
        text="Is this file important?",
        style="Question.TLabel"
    ).pack(pady=(30, 20))

    knop_frame = ttk.Frame(stap1)
    knop_frame.pack()

    #################################################################
    # STAP 2
    #################################################################

    stap2 = ttk.Frame(hoofd)

    onderwerp_var = tk.StringVar()
    status_var = tk.StringVar(value="in progress")
    betrouwbaarheid_var = tk.IntVar(value=5)

    bovenste_rij = ttk.Frame(stap2)
    bovenste_rij.pack(fill="x")

    onderwerp_kader = ttk.LabelFrame(
        bovenste_rij,
        text="Topic",
        padding=12
    )

    onderwerp_kader.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 10)
    )

    combo = ttk.Combobox(
        onderwerp_kader,
        textvariable=onderwerp_var,
        values=haal_onderwerpen()
    )

    combo.pack(fill="x")

    ttk.Label(
        onderwerp_kader,
        text="Choose or type a topic",
        style="Muted.TLabel"
    ).pack(anchor="w", pady=(4, 0))

    status_kader = ttk.LabelFrame(
        bovenste_rij,
        text="Status",
        padding=12
    )

    status_kader.pack(side="left")

    ttk.Radiobutton(
        status_kader,
        text="In progress",
        variable=status_var,
        value="in progress"
    ).pack(anchor="w")

    ttk.Radiobutton(
        status_kader,
        text="Done",
        variable=status_var,
        value="done"
    ).pack(anchor="w")

    betrouwbaarheid_kader = ttk.LabelFrame(
        stap2,
        text="Reliability",
        padding=12
    )

    betrouwbaarheid_kader.pack(
        fill="x",
        pady=(15, 15)
    )

    waarde_label = ttk.Label(
        betrouwbaarheid_kader,
        text="5 / 10",
        style="Value.TLabel"
    )

    waarde_label.pack()

    def bij_schuif(waarde):
        getal = round(float(waarde))

        betrouwbaarheid_var.set(getal)

        kleur = "#d32f2f"

        if getal >= 4:
            kleur = "#f9a825"

        if getal >= 7:
            kleur = "#2e7d32"

        waarde_label.config(
            text=f"{getal} / 10",
            foreground=kleur
        )

    schaal = ttk.Scale(
        betrouwbaarheid_kader,
        from_=1,
        to=10,
        orient="horizontal",
        command=bij_schuif,
        length=400
    )

    schaal.set(5)
    schaal.pack(fill="x", pady=8)

    onder_scale = ttk.Frame(betrouwbaarheid_kader)
    onder_scale.pack(fill="x")

    ttk.Label(
        onder_scale,
        text="Not reliable",
        style="Muted.TLabel"
    ).pack(side="left")

    ttk.Label(
        onder_scale,
        text="Very reliable",
        style="Muted.TLabel"
    ).pack(side="right")

    def bij_opslaan(_event=None):
        onderwerp = onderwerp_var.get().strip()

        if not onderwerp:
            messagebox.showwarning(
                "Topic missing",
                "Please choose or type a topic.",
                parent=root
            )
            combo.focus_set()
            return

        opslaan(
            bestandspad,
            onderwerp,
            status_var.get(),
            betrouwbaarheid_var.get()
        )

        opgeslagen["waarde"] = True

        root.destroy()

    onderste = ttk.Frame(stap2)
    onderste.pack(
        fill="x",
        pady=(10, 0)
    )

    ttk.Button(
        onderste,
        text="Cancel",
        command=root.destroy
    ).pack(side="right")

    ttk.Button(
        onderste,
        text="Save",
        style="Big.TButton",
        command=bij_opslaan
    ).pack(side="right", padx=10)

    def bij_ja():
        stap1.pack_forget()

        stap_label.config(text="Step 2 of 2")

        stap2.pack(
            fill="both",
            expand=True
        )

        combo.focus_set()

        root.bind("<Return>", bij_opslaan)

    ttk.Button(
        knop_frame,
        text="Yes",
        style="Big.TButton",
        command=bij_ja
    ).pack(side="left", padx=10)

    ttk.Button(
        knop_frame,
        text="No",
        style="Big.TButton",
        command=root.destroy
    ).pack(side="left", padx=10)

    root.bind("<Escape>", lambda e: root.destroy())

    _centreer(root)

    root.mainloop()

    return opgeslagen["waarde"]


if __name__ == "__main__":
    init_db()
    toon_popup(r"C:\documenten\rapport.pdf")