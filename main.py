import flet as ft
import threading
import speech_recognition as sr
import time
import geocoder      
import sounddevice as sd 
import soundfile as sf
import numpy as np
import json
import os

# Nome do arquivo de memória
CONFIG_FILE = "config_sentinela.json"

# --- 1. MÓDULO DE PERÍCIA E EVIDÊNCIAS ---

def iniciar_coleta_sentinela(status_text, page):
    reconhecedor_pos = sr.Recognizer()
    audio_total = []
    fs = 44100
    
    try:
        g = geocoder.ip('me')
        print(f"\n[SENTINELA NEURAL] Evento Georreferenciado: {g.latlng}")
    except:
        pass

    with sr.Microphone() as source:
        while "ALERTA" in status_text.value or "EMERGÊNCIA" in status_text.value:
            try:
                audio_bloco = reconhecedor_pos.listen(source, phrase_time_limit=5)
                texto = reconhecedor_pos.recognize_google(audio_bloco, language="pt-BR")
                print(f"[EVIDÊNCIA VOCAL]: {texto}")
                
                status_text.value = f"EMERGÊNCIA ATIVA: {texto[:30]}..."
                page.update()

                dados_audio = np.frombuffer(audio_bloco.get_raw_data(), dtype=np.int16)
                audio_total.append(dados_audio)
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"Erro no monitoramento: {e}")
                break

    if audio_total:
        audio_final = np.concatenate(audio_total)
        nome_arq = f"SENTINELA_PROVA_{int(time.time())}.wav"
        sf.write(nome_arq, audio_final.astype(np.float32) / 32768.0, fs)
        print(f"\n[!] ARQUIVO DE PERÍCIA GERADO: {nome_arq}")
        
    status_text.value = "SENTINELA DESATIVADO - DADOS SALVOS"
    page.update()

# --- 2. MÓDULO DE VIGÍLIA ---

def iniciar_vigilia(status_text, icone_stack, page, gatilhos):
    reconhecedor = sr.Recognizer()
    with sr.Microphone() as source:
        reconhecedor.adjust_for_ambient_noise(source, duration=1)
        status_text.value = "SENTINELA EM VIGÍLIA SILENCIOSA"
        page.update()
        
        while True:
            if "DESATIVADO" in status_text.value:
                break
            try:
                audio = reconhecedor.listen(source, phrase_time_limit=4)
                texto_captado = reconhecedor.recognize_google(audio, language="pt-BR").lower()

                if any(frase in texto_captado for frase in gatilhos):
                    status_text.value = "!!! ALERTA ATIVADO !!!"
                    status_text.color = ft.colors.YELLOW
                    icone_stack.controls[0].color = ft.colors.YELLOW 
                    page.update()
                    iniciar_coleta_sentinela(status_text, page)
                    break 
            except:
                pass

# --- 3. INTERFACE SENTINELANEURAL ---

def main(page: ft.Page):
    page.title = "SentinelaNeural"
    page.window_width = 450
    page.window_height = 750
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Dados Globais
    config_data = {"gatilhos": [], "perfil_selecionado": "", "nome_agressor": ""}
    
    PERFIS = {
        "Assalto/Sequestro": ["passa o grana","passa o relogio","passa o celular", "pedeu plaboy","perdeu","perdeu perdeu", "não reage", "nao reaja","fica quieto"],
        "Violência Doméstica": ["help","para com isso", "me deixa em paz", "não encosta em mim", "sai daqui"],
        "Acidentes/Saúde": ["socorro", "ajuda", "estou passando mal", "não consigo respirar"],
        "Segurança Total": []
    }
    
    todas_frases = []
    for p in PERFIS.values(): todas_frases.extend(p)
    PERFIS["Segurança Total"] = list(set(todas_frases))

    def criar_logo(tamanho_brain, tamanho_shield, cor_brain):
        return ft.Stack(
            controls=[
                ft.Icon(name=ft.icons.PSYCHOLOGY, size=tamanho_brain, color=cor_brain),
                ft.Icon(
                    name=ft.icons.SHIELD_SHARP, 
                    size=tamanho_shield, 
                    color=ft.colors.RED_700,
                    offset=ft.Offset(0.4, 0.4)
                ),
            ],
            width=tamanho_brain + 20,
            height=tamanho_brain + 10,
        )

    # --- FUNÇÕES DE MEMÓRIA (SALVAR/CARREGAR) ---

    def salvar_memoria(perfil, nome):
        dados = {"perfil": perfil, "nome": nome}
        with open(CONFIG_FILE, "w") as f:
            json.dump(dados, f)

    def carregar_memoria():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except:
                return None
        return None

    def aplicar_configuracoes(perfil, nome):
        config_data["perfil_selecionado"] = perfil
        config_data["nome_agressor"] = nome
        config_data["gatilhos"] = list(PERFIS[perfil])
        if nome:
            nome_limpo = nome.lower()
            config_data["gatilhos"].extend([f"para com isso {nome_limpo}", f"sai daqui {nome_limpo}"])
        exibir_monitoramento()

    def botao_salvar_click(e):
        salvar_memoria(dd_perfil.value, campo_nome.value)
        aplicar_configuracoes(dd_perfil.value, campo_nome.value)

    def exibir_config(e=None):
        page.clean()
        page.add(
            criar_logo(80, 40, ft.colors.WHITE),
            ft.Text("SENTINELANEURAL", size=28, weight="bold", color="red"),
            ft.Text("CONFIGURAÇÃO DE PROTEÇÃO", size=14, color="grey"),
            ft.Container(height=20),
            dd_perfil,
            ft.Text("Nome do agressor (se conhecido):", size=14),
            campo_nome,
            ft.Divider(height=40, color="transparent"),
            ft.ElevatedButton(
                "SALVAR E ATIVAR", bgcolor="red", color="white", width=300, height=50, on_click=botao_salvar_click
            )
        )

    def exibir_monitoramento():
        page.clean()
        status_text = ft.Text("SENTINELA DESATIVADO", size=16, color="grey")
        logo_monitor = criar_logo(120, 60, ft.colors.GREY_700)

        def ligar_sentinela(e):
            if btn_p.text == "LIGAR PROTEÇÃO":
                btn_p.text = "DESATIVAR"; btn_p.bgcolor = ft.colors.RED
                status_text.value = "INICIALIZANDO VIGÍLIA..."
                status_text.color = ft.colors.WHITE
                logo_monitor.controls[0].color = ft.colors.RED_ACCENT 
                page.update()
                threading.Thread(target=iniciar_vigilia, args=(status_text, logo_monitor, page, config_data["gatilhos"]), daemon=True).start()
            else:
                btn_p.text = "LIGAR PROTEÇÃO"; btn_p.bgcolor = "green"
                status_text.value = "SISTEMA DESATIVADO"; status_text.color = "grey"
                logo_monitor.controls[0].color = ft.colors.GREY_700
                page.update()

        btn_p = ft.ElevatedButton("LIGAR PROTEÇÃO", bgcolor="green", color="white", width=260, height=55, on_click=ligar_sentinela)
        
        page.add(
            ft.IconButton(ft.icons.SETTINGS_OUTLINED, on_click=exibir_config),
            logo_monitor,
            ft.Text("SENTINELANEURAL", size=30, weight="bold", color="red"),
            ft.Text("VIGÍLIA INTELIGENTE ATIVA", size=10, italic=True),
            ft.Container(height=30),
            status_text,
            ft.Container(height=40),
            btn_p,
            ft.Text(f"Perfil: {config_data['perfil_selecionado']}", size=11, color="grey")
        )

    # Inicialização dos componentes
    dd_perfil = ft.Dropdown(width=300, value="Assalto/Sequestro", options=[ft.dropdown.Option(k) for k in PERFIS.keys()], border_color="red")
    campo_nome = ft.TextField(label="Apelido/Nome", width=300, border_color="red")

    # --- LÓGICA DE AUTO-LOAD ---
    memoria = carregar_memoria()
    if memoria:
        aplicar_configuracoes(memoria["perfil"], memoria["nome"])
    else:
        exibir_config()

ft.app(target=main)